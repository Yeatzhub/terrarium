# 📱 Hilt Dependency Injection Patterns

**Focus:** Scoping, Qualifiers, Assisted Injection, Multi-Module Setup
**Pattern:** Clean dependency graph with lifecycle-aware scoping

---

## 1. Component Hierarchy

```
SingletonComponent      (App lifecycle)
├── ApplicationContext
├── Database
├── Repository (Singleton)
│   └── ApiService
│
└── ActivityRetainedComponent (Survives rotation)
    ├── ViewModel
    │   └── SavedStateHandle
    │
    └── ActivityComponent
        ├── ActivityContext
        ├── NavController
        └── FragmentComponent
            └── ViewComponent
```

---

## 2. Core Module Setup

```kotlin
// Module providing app-wide singletons
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(
        cache: Cache,
        loggingInterceptor: HttpLoggingInterceptor
    ): OkHttpClient = OkHttpClient.Builder()
        .cache(cache)
        .addInterceptor(loggingInterceptor)
        .addInterceptor(AuthInterceptor())
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
        .build()
    
    @Provides
    @Singleton
    fun provideTradingApi(retrofit: Retrofit): TradingApi = 
        retrofit.create(TradingApi::class.java)
    
    @Provides
    @Singleton
    fun provideCache(@ApplicationContext context: Context): Cache =
        Cache(context.cacheDir, 50 * 1024 * 1024) // 50MB
}

// Database Module
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): TradingDatabase =
        Room.databaseBuilder(context, TradingDatabase::class.java, "trading.db")
            .build()
    
    @Provides
    fun provideAssetDao(db: TradingDatabase): AssetDao = db.assetDao()
    
    @Provides
    fun providePriceDao(db: TradingDatabase): PriceDao = db.priceDao()
}

// Repository Module
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    
    @Binds
    @Singleton
    abstract fun bindPriceRepository(
        impl: PriceRepositoryImpl
    ): PriceRepository
    
    @Binds
    @Singleton
    abstract fun bindTradingRepository(
        impl: TradingRepositoryImpl
    ): TradingRepository
}
```

---

## 3. Qualifiers for Multiple Instances

```kotlin
// Define qualifiers
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class DefaultDispatcher

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class MainDispatcher

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class ApplicationScope

// Provide qualified instances
@Module
@InstallIn(SingletonComponent::class)
object CoroutineModule {
    
    @Provides
    @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
    
    @Provides
    @DefaultDispatcher
    fun provideDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
    
    @Provides
    @MainDispatcher
    fun provideMainDispatcher(): CoroutineDispatcher = Dispatchers.Main
    
    @Provides
    @Singleton
    @ApplicationScope
    fun provideApplicationScope(
        @DefaultDispatcher defaultDispatcher: CoroutineDispatcher
    ): CoroutineScope = CoroutineScope(
        SupervisorJob() + defaultDispatcher
    )
}

// Usage in classes
class PriceRepository @Inject constructor(
    private val api: TradingApi,
    private val dao: PriceDao,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
    @ApplicationScope private val scope: CoroutineScope
)

// Multiple instances of same type
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class AuthInterceptorOkHttp

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class PublicOkHttp

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    @AuthInterceptorOkHttp
    fun provideAuthOkHttpClient(
        authInterceptor: AuthInterceptor
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .build()
    
    @Provides
    @Singleton
    @PublicOkHttp
    fun providePublicOkHttpClient(): OkHttpClient = OkHttpClient.Builder().build()
    
    @Provides
    @Singleton
    fun provideAuthenticatedApi(
        @AuthInterceptorOkHttp client: OkHttpClient
    ): AuthenticatedApi = Retrofit.Builder()
        .client(client)
        .build()
        .create(AuthenticatedApi::class.java)
    
    @Provides
    @Singleton
    fun providePublicApi(
        @PublicOkHttp client: OkHttpClient
    ): PublicApi = Retrofit.Builder()
        .client(client)
        .build()
        .create(PublicApi::class.java)
}
```

---

## 4. Assisted Injection (Factory Pattern)

```kotlin
// When you need runtime parameters WITH dependencies
class PriceChartViewModel @AssistedInject constructor(
    private val repository: PriceRepository,
    private val analytics: AnalyticsTracker,
    @Assisted private val assetId: String,
    @Assisted private val timeframe: TimeFrame
) : ViewModel() {
    
    @AssistedFactory
    interface Factory {
        fun create(assetId: String, timeframe: TimeFrame): PriceChartViewModel
    }
    
    init {
        analytics.track("chart_viewed", mapOf("asset" to assetId))
    }
}

// ViewModel with SavedStateHandle
class TradeViewModel @AssistedInject constructor(
    private val repository: TradingRepository,
    private val savedStateHandle: SavedStateHandle,
    @Assisted private val initialSymbol: String
) : ViewModel() {
    
    @AssistedFactory
    interface Factory {
        fun create(initialSymbol: String): TradeViewModel
    }
}

// Usage in Compose
@Composable
fun PriceChartScreen(
    assetId: String,
    timeframe: TimeFrame,
    viewModel: PriceChartViewModel = hiltViewModel(
        creationCallback = { factory: PriceChartViewModel.Factory ->
            factory.create(assetId, timeframe)
        }
    )
) {
    // UI implementation
}

// Assisted injection for non-ViewModel classes
class WebSocketManager @AssistedInject constructor(
    private val client: OkHttpClient,
    private val json: Json,
    @Assisted private val symbols: List<String>,
    @Assisted private val onMessage: (PriceUpdate) -> Unit
) {
    @AssistedFactory
    interface Factory {
        fun create(
            symbols: List<String>,
            onMessage: (PriceUpdate) -> Unit
        ): WebSocketManager
    }
    
    fun connect() { /* ... */ }
}

// Usage
class PriceRepository @Inject constructor(
    private val webSocketFactory: WebSocketManager.Factory
) {
    fun observePrices(symbols: List<String>): Flow<PriceUpdate> = callbackFlow {
        val manager = webSocketFactory.create(symbols) { update ->
            trySend(update)
        }
        manager.connect()
        awaitClose { /* cleanup */ }
    }
}
```

---

## 5. Component Scoping

```kotlin
// Singleton (application lifecycle)
@Singleton
class TradingRepository @Inject constructor(
    private val api: TradingApi
)

// ActivityRetained (survives config changes)
@ActivityRetainedScoped
class TradingUseCases @Inject constructor(
    private val repository: TradingRepository
) {
    // Use cases survive rotation
}

// ActivityScoped
@ActivityScoped
class Navigator @Inject constructor(
    private val activity: Activity
)

// FragmentScoped
@FragmentScoped
class ChartRenderer @Inject constructor(
    private val context: Context
)

// ServiceScoped
@ServiceScoped
class SyncWorker @Inject constructor(
    private val repository: TradingRepository
) {
    // Used in background service
}

// Custom component for feature modules
@Scope
@Retention(AnnotationRetention.RUNTIME)
annotation class FeatureScope

@DefineComponent(parent = SingletonComponent::class)
interface FeatureComponent

@DefineComponent.Builder
interface FeatureComponentBuilder {
    fun setFeatureId(@BindsInstance @FeatureId featureId: String): FeatureComponentBuilder
    fun build(): FeatureComponent
}

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class FeatureId
```

---

## 6. Entry Points (Components Without Injection)

```kotlin
// For classes not created by Hilt (BroadcastReceiver, workers, etc.)
class PriceBroadcastReceiver : BroadcastReceiver() {
    
    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface PriceEntryPoint {
        fun priceRepository(): PriceRepository
        fun notificationManager(): NotificationManager
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        val entryPoint = EntryPointAccessors.fromApplication(
            context,
            PriceEntryPoint::class.java
        )
        
        val repository = entryPoint.priceRepository()
        
        // Use repository...
    }
}

// Custom View with injection
@AndroidEntryPoint
class PriceChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {
    
    @Inject
    lateinit var chartRenderer: ChartRenderer
    
    @Inject
    @IoDispatcher
    lateinit var ioDispatcher: CoroutineDispatcher
}

// ContentProvider with Hilt
@EntryPoint
@InstallIn(SingletonComponent::class)
interface ContentProviderEntryPoint {
    fun assetDao(): AssetDao
}

class TradingContentProvider : ContentProvider() {
    private lateinit var dao: AssetDao
    
    override fun onCreate(): Boolean {
        val entryPoint = EntryPointAccessors.fromApplication(
            requireNotNull(context),
            ContentProviderEntryPoint::class.java
        )
        dao = entryPoint.assetDao()
        return true
    }
}

// WorkManager with Hilt
@HiltWorker
class PriceSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val repository: PriceRepository
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        return try {
            repository.sync()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}

// Register worker
@HiltAndroidApp
class TradingApplication : Application(), Configuration.Provider {
    @Inject
    lateinit var workerFactory: HiltWorkerFactory
    
    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
}
```

---

## 7. Multi-Module Setup

```kotlin
// :core:di module (shared)
// CoreModule.kt
@Module
@InstallIn(SingletonComponent::class)
object CoreModule {
    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }
}

// :features:trading module
// TradingModule.kt
@Module
@InstallIn(ViewModelComponent::class)
object TradingModule {
    
    @Provides
    @ViewModelScoped
    fun provideChartCalculator(
        @ApplicationContext context: Context
    ): ChartCalculator = ChartCalculator(context)
}

// :features:portfolio module
// PortfolioModule.kt
@Module
@InstallIn(ViewModelComponent::class)
abstract class PortfolioModule {
    
    @Binds
    @ViewModelScoped
    abstract fun bindPortfolioCalculator(
        impl: PortfolioCalculatorImpl
    ): PortfolioCalculator
}

// Gradle setup
// build.gradle.kts (app module)
dependencies {
    implementation(project(":core:di"))
    implementation(project(":core:network"))
    implementation(project(":features:trading"))
    implementation(project(":features:portfolio"))
    
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-compiler:2.48")
}

// build.gradle.kts (feature module)
plugins {
    id("com.google.dagger.hilt.android")
}

dependencies {
    implementation(project(":core:di"))
    implementation(project(":core:domain"))
    
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-compiler:2.48")
}

// Aggregation module for navigation
@Module
@InstallIn(SingletonComponent::class)
abstract class NavigationModule {
    
    @Binds
    @IntoSet
    abstract fun bindTradingNavigator(navigator: TradingNavigator): Navigator
    
    @Binds
    @IntoSet
    abstract fun bindPortfolioNavigator(navigator: PortfolioNavigator): Navigator
}

// Collect all navigators
class NavigationRouter @Inject constructor(
    private val navigators: Set<@JvmSuppressWildcards Navigator>
)
```

---

## 8. Testing with Hilt

```kotlin
// Test dependencies
dependencies {
    testImplementation("com.google.dagger:hilt-android-testing:2.48")
    kaptTest("com.google.dagger:hilt-compiler:2.48")
    
    androidTestImplementation("com.google.dagger:hilt-android-testing:2.48")
    kaptAndroidTest("com.google.dagger:hilt-compiler:2.48")
}

// Test module for fakes
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [NetworkModule::class]
)
object TestNetworkModule {
    
    @Provides
    @Singleton
    fun provideFakeTradingApi(): TradingApi = FakeTradingApi()
}

// Test with Hilt
@HiltAndroidTest
class PriceRepositoryTest {
    
    @get:Rule(order = 0)
    var hiltRule = HiltAndroidRule(this)
    
    @get:Rule(order = 1)
    val mainDispatcherRule = MainDispatcherRule()
    
    @Inject
    lateinit var repository: PriceRepository
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun testWithFakeApi() = runTest {
        // Uses FakeTradingApi automatically
        val prices = repository.getPrices()
        assertNotNull(prices)
    }
}

// Custom test application
@CustomTestApplication(TradingApplication::class)
interface HiltTestApplication

// Robolectric test
@HiltAndroidTest
@Config(application = HiltTestApplication_Application::class)
@RunWith(RobolectricTestRunner::class)
class ViewModelTest {
    
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @Inject
    lateinit var viewModelFactory: ViewModelProvider.Factory
    
    @Test
    fun testViewModel() {
        hiltRule.inject()
        
        val viewModel = ViewModelProvider(
            viewModelStore,
            viewModelFactory
        )[TradeViewModel::class.java]
        
        // Test viewModel...
    }
}

// Uninstall modules for specific tests
@HiltAndroidTest
@UninstallModules(NetworkModule::class)
class NoNetworkTest {
    
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    // NetworkModule replaced with nothing
}
```

---

## 9. Best Practices

```kotlin
// ✅ DO: Use constructor injection
class Repository @Inject constructor(
    private val api: Api
) // Dependencies explicit and testable

// ❌ DON'T: Use field injection
@Inject lateinit var api: Api // Harder to test, null safety issues

// ✅ DO: Scope to lowest appropriate component
@ActivityRetainedScoped // ViewModels
@ActivityScoped // Activity-specific
@Singleton // Application-wide

// ❌ DON'T: Over-scope
@Singleton // Don't make everything singleton
class ChartRenderer // Only needed for chart screen

// ✅ DO: Use `@Binds` for interfaces
@Binds
abstract fun bindRepo(impl: RepositoryImpl): Repository

// ❌ DON'T: Use `@Provides` for simple bindings
@Provides
fun bindRepo(impl: RepositoryImpl): Repository = impl // Unnecessary

// ✅ DO: Qualify when multiple instances needed
@IoDispatcher vs @MainDispatcher

// ✅ DO: Use assisted injection for runtime params
@AssistedInject for ViewModel factories

// ❌ DON'T: Pass context unnecessarily
// Bad: Pass context through 5 layers
// Good: Use @ApplicationContext or @ActivityContext

// ✅ DO: Inject dispatchers (testability)
@Inject
@IoDispatcher
lateinit var dispatcher: CoroutineDispatcher

// ✅ DO: Create modules per layer
NetworkModule, DatabaseModule, RepositoryModule

// ✅ DO: Use entry points for non-Hilt classes
EntryPointAccessors.fromApplication()
```

---

## TL;DR

| Pattern | Use Case |
|---------|----------|
| `@Singleton` | Application-wide state |
| `@ActivityRetainedScoped` | ViewModel scope (survives rotation) |
| `@AssistedInject` | Runtime params + dependencies |
| `@Qualifier` | Multiple instances of same type |
| `@Binds` | Interface → Implementation |
| `@EntryPoint` | Non-Hilt class injection |
| `@TestInstallIn` | Replace modules in tests |
| `@HiltWorker` | WorkManager integration |

**Scoping Rule:** Scope to the lowest component possible. Constructor injection > field injection. `@Binds` for interfaces, `@Provides` for concrete types requiring construction logic.
