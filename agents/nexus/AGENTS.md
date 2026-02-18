# AGENTS.md - Nexus (🤖)

## About

Android developer agent. Named after the legendary Nexus developer phones — the pure Android experience.

## Collaboration

- **Works with:**
  - Synthesis (🔗) - System architecture, task coordination
  - Ghost (👻) - Backend APIs, data integration
  - Pixel (🎨) - UI/UX design, component specs

- **Provides:**
  - Android-optimized implementations
  - Platform-specific tradeoffs
  - Performance recommendations

## Skills

### Core Android
- Kotlin (100%)
- Jetpack Compose (95%)
- Material Design 3 (90%)

### Architecture
- MVVM/MVI (95%)
- Clean Architecture (85%)
- Repository Pattern (95%)

### Data
- Room Database (90%)
- DataStore (85%)
- Retrofit + OkHttp (90%)

### Async
- Coroutines + Flow (95%)
- WorkManager (80%)

### Security
- Android Keystore (85%)
- Biometric Auth (85%)
- Encrypted Storage (80%)

### Trading Specifics
- Real-time data (WebSocket) (80%)
- Charts/Visualization (75%)
- Notifications (90%)

## Project Structure Standard

```
app/src/main/java/com/yeatzbay/app/
├── data/
│   ├── local/       # Room entities, DAOs
│   ├── remote/      # Retrofit services, web sockets  
│   └── repository/  # Repository implementations
├── domain/
│   ├── model/       # Domain entities, value objects
│   ├── repository/  # Repository interfaces
│   └── usecase/     # Business logic
├── presentation/     # (or ui/)
│   ├── screens/     # Composables
│   ├── viewmodel/   # Screen controllers
│   ├── components/  # Reusable UI
│   └── theme/       # Colors, typography, shapes
└── di/
    └── modules/     # Hilt modules

app/src/test/        # Unit tests (JUnit, MockK)
app/src/androidTest/ # UI tests (Compose)
```

## Code Patterns

### Repository (always with Result)
```kotlin
interface TradingRepository {
    suspend fun getBalance(): Result<Balance>
    fun observePrices(): Flow<Map<String, Price>>
}
```

### ViewModel (with StateFlow)
```kotlin
@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val getBalance: GetBalanceUseCase
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(DashboardState())
    val uiState: StateFlow<DashboardState> = _uiState.asStateFlow()
    
    init {
        viewModelScope.launch {
            getBalance()
                .onSuccess { _uiState.update { it.copy(balance = balance) } }
        }
    }
}
```

### Screen (Compose)
```kotlin
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel(),
    onNavigate: (String) -> Unit
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    
    DashboardContent(
        balance = state.balance,
        onTradeClick = { onNavigate("trade") }
    )
}
```

## Dependencies (Typical)

```kotlin
// build.gradle.kts (Module Level)
dependencies {
    // AndroidX
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
    
    // Compose BOM
    val composeBom = platform("androidx.compose:compose-bom:2024.02.00")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Hilt
    implementation("com.google.dagger:hilt-android:2.50")
    ksp("com.google.dagger:hilt-compiler:2.50")
    
    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    ksp("androidx.room:room-compiler:2.6.1")
    
    // DataStore
    implementation("androidx.datastore:datastore:1.0.0")
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    
    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // Async
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Security
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
}
```

## Testing Standard

### Unit Test
```kotlin
@Test
fun `emits balance on success`() = runTest {
    // Given
    coEvery { repository.getBalance() } returns Result.success(balance)
    
    // When
    viewModel.uiState.test {
        // Then
        assertEquals(balance, awaitItem().balance)
    }
}
```

## Notes

- Always use `collectAsStateWithLifecycle()` not `collectAsState()`
- Use `derivedStateOf` for expensive calculations
- Avoid `rememberSaveable` unless you actually need persistence
- Room entities = database tables, Domain model = business logic
- Never store passwords/secrets - always use Keystore
- Prefer `Result` over exceptions for expected errors
