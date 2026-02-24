# Android Architecture - MVVM with Hilt & Testing

## Overview
Production MVVM architecture with clean separation, dependency injection, and testable design.

## Project Structure

```
app/
├── data/
│   ├── remote/
│   │   └── ApiService.kt
│   ├── local/
│   │   ├── AppDatabase.kt
│   │   └── dao/
│   ├── repository/
│   │   └── UserRepositoryImpl.kt
│   └── di/
│       └── DataModule.kt
├── domain/
│   ├── model/
│   │   └── User.kt
│   └── repository/
│       └── UserRepository.kt
├── presentation/
│   ├── user/
│   │   ├── UserViewModel.kt
│   │   └── UserScreen.kt
│   └── di/
│       └── ViewModelModule.kt
└── MainActivity.kt
```

## 1. Domain Layer (Pure Kotlin)

```kotlin
// domain/model/User.kt
@JvmInline
value class UserId(val value: String)

@Immutable
data class User(
    val id: UserId,
    val name: String,
    val email: String
)

// domain/repository/UserRepository.kt
interface UserRepository {
    fun observeUser(id: UserId): Flow<Result<User>>
    suspend fun updateUser(user: User): Result<Unit>
    suspend fun refreshUser(id: UserId): Result<User>
}
```

## 2. Data Layer (Implementation)

```kotlin
// data/local/UserDao.kt
@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id")
    fun observe(id: String): Flow<UserEntity?>
    
    @Upsert
    suspend fun upsert(user: UserEntity)
    
    @Query("DELETE FROM users WHERE id = :id")
    suspend fun delete(id: String)
}

// data/remote/UserApi.kt
interface UserApi {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: String): UserDto
    
    @PATCH("users/{id}")
    suspend fun updateUser(@Path("id") id: String, @Body user: UserDto)
}

// data/repository/UserRepositoryImpl.kt
class UserRepositoryImpl @Inject constructor(
    private val api: UserApi,
    private val dao: UserDao,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) : UserRepository {
    
    override fun observeUser(id: UserId): Flow<Result<User>> = channelFlow {
        // 1. Emit cached data immediately
        launch {
            dao.observe(id.value)
                .filterNotNull()
                .map { it.toDomain() }
                .collect { send(Result.success(it)) }
        }
        
        // 2. Fetch fresh data
        launch {
            val result = refreshUser(id)
            if (result.isFailure) {
                send(Result.failure(result.exceptionOrNull()!!))
            }
        }
    }
        .flowOn(ioDispatcher)
        .catch { emit(Result.failure(it)) }
    
    override suspend fun updateUser(user: User): Result<Unit> = withContext(ioDispatcher) {
        runCatching {
            api.updateUser(user.id.value, user.toDto())
            dao.upsert(user.toEntity())
        }
    }
    
    override suspend fun refreshUser(id: UserId): Result<User> = withContext(ioDispatcher) {
        runCatching {
            val dto = api.getUser(id.value)
            val entity = dto.toEntity()
            dao.upsert(entity)
            entity.toDomain()
        }
    }
}
```

## 3. Presentation Layer (MVVM)

```kotlin
// presentation/user/UserViewModel.kt
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repository: UserRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    
    // Extract navigation args
    private val userId: UserId = UserId(
        savedStateHandle.get<String>("userId") ?: ""
    )
    
    // UI State - single source of truth
    sealed interface UiState {
        data object Loading : UiState
        data class Success(val user: User, val isEditing: Boolean = false) : UiState
        data class Error(val message: String) : UiState
    }
    
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    // Events from UI
    sealed interface Event {
        data class UpdateName(val name: String) : Event
        data class UpdateEmail(val email: String) : Event
        data object Save : Event
        data object ToggleEdit : Event
        data object Retry : Event
    }
    
    init {
        observeUser()
    }
    
    fun onEvent(event: Event) {
        when (event) {
            is Event.UpdateName -> updateName(event.name)
            is Event.UpdateEmail -> updateEmail(event.email)
            Event.Save -> saveUser()
            Event.ToggleEdit -> toggleEdit()
            Event.Retry -> observeUser()
        }
    }
    
    private fun observeUser() {
        viewModelScope.launch {
            repository.observeUser(userId).collect { result ->
                _uiState.value = result.fold(
                    onSuccess = { UiState.Success(it) },
                    onFailure = { UiState.Error(it.message ?: "Unknown error") }
                )
            }
        }
    }
    
    private fun updateName(name: String) {
        val current = (_uiState.value as? UiState.Success) ?: return
        _uiState.value = current.copy(user = current.user.copy(name = name))
    }
    
    private fun updateEmail(email: String) {
        val current = (_uiState.value as? UiState.Success) ?: return
        _uiState.value = current.copy(user = current.user.copy(email = email))
    }
    
    private fun toggleEdit() {
        val current = (_uiState.value as? UiState.Success) ?: return
        _uiState.value = current.copy(isEditing = !current.isEditing)
    }
    
    private fun saveUser() {
        val current = (_uiState.value as? UiState.Success) ?: return
        viewModelScope.launch {
            repository.updateUser(current.user)
                .onSuccess { 
                    _uiState.value = current.copy(isEditing = false)
                }
                .onFailure {
                    _uiState.value = UiState.Error(it.message ?: "Save failed")
                }
        }
    }
}
```

## 4. Hilt DI Modules

```kotlin
// data/di/DataModule.kt
@Module
@InstallIn(SingletonComponent::class)
object DataModule {
    
    @Provides @Singleton
    fun provideDatabase(app: Application): AppDatabase =
        Room.databaseBuilder(app, AppDatabase::class.java, "app.db")
            .addMigrations(/* migrations */)
            .build()
    
    @Provides
    fun provideUserDao(db: AppDatabase): UserDao = db.userDao()
    
    @Provides @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl("https://api.example.com/")
        .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
        .build()
    
    @Provides
    fun provideUserApi(retrofit: Retrofit): UserApi = retrofit.create(UserApi::class.java)
    
    @Binds
    fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}

// di/DispatcherModule.kt
@Module
@InstallIn(SingletonComponent::class)
object DispatcherModule {
    @Provides @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
}

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher
```

## 5. Comprehensive Testing

```kotlin
// Unit test - ViewModel
@OptIn(ExperimentalCoroutinesApi::class)
class UserViewModelTest {
    
    @get:Rule
    val dispatcherRule = StandardTestDispatcher()
    
    private val repository = mockk<UserRepository>()
    private lateinit var viewModel: UserViewModel
    
    @Before
    fun setup() {
        every { repository.observeUser(UserId("123")) } returns flowOf(
            Result.success(User(UserId("123"), "John", "john@test.com"))
        )
    }
    
    @Test
    fun `init loads user successfully`() = runTest {
        // Given
        val savedState = savedStateHandleOf("userId" to "123")
        
        // When
        viewModel = UserViewModel(repository, savedState)
        advanceUntilIdle()
        
        // Then
        val state = viewModel.uiState.value
        assertTrue(state is UserViewModel.UiState.Success)
        assertEquals("John", (state as UserViewModel.UiState.Success).user.name)
    }
    
    @Test
    fun `saveUser updates repository and exits edit mode`() = runTest {
        // Given
        coEvery { repository.updateUser(any()) } returns Result.success(Unit)
        val savedState = savedStateHandleOf("userId" to "123")
        viewModel = UserViewModel(repository, savedState)
        advanceUntilIdle()
        
        // When
        viewModel.onEvent(UserViewModel.Event.ToggleEdit)
        viewModel.onEvent(UserViewModel.Event.UpdateName("Jane"))
        viewModel.onEvent(UserViewModel.Event.Save)
        advanceUntilIdle()
        
        // Then
        val state = viewModel.uiState.value as UserViewModel.UiState.Success
        assertEquals("Jane", state.user.name)
        assertFalse(state.isEditing)
        coVerify { repository.updateUser(match { it.name == "Jane" }) }
    }
}

// Unit test - Repository
class UserRepositoryImplTest {
    
    private val api = mockk<UserApi>()
    private val dao = mockk<UserDao>(relaxed = true)
    private val testDispatcher = StandardTestDispatcher()
    
    private val repository = UserRepositoryImpl(api, dao, testDispatcher)
    
    @Test
    fun `refreshUser fetches from API and caches`() = runTest {
        // Given
        every { api.getUser("123") } returns UserDto("123", "John", "john@test.com")
        
        // When
        val result = repository.refreshUser(UserId("123"))
        
        // Then
        assertTrue(result.isSuccess)
        assertEquals("John", result.getOrThrow().name)
        coVerify { dao.upsert(match { it.id == "123" && it.name == "John" }) }
    }
}

// UI test - Compose
@RunWith(AndroidJUnit4::class)
class UserScreenTest {
    
    @get:Rule
    val composeRule = createComposeRule()
    
    @Test
    fun displaysUserName() {
        val state = UserViewModel.UiState.Success(
            User(UserId("123"), "John Doe", "john@test.com")
        )
        
        composeRule.setContent {
            MaterialTheme {
                UserScreenContent(
                    state = state,
                    onEvent = {}
                )
            }
        }
        
        composeRule.onNodeWithText("John Doe").assertIsDisplayed()
    }
    
    @Test
    fun editModeShowsEditableFields() {
        val state = UserViewModel.UiState.Success(
            User(UserId("123"), "John", "john@test.com"),
            isEditing = true
        )
        
        composeRule.setContent {
            MaterialTheme {
                UserScreenContent(state = state, onEvent = {})
            }
        }
        
        composeRule.onNodeWithText("John")
            .assert(hasSetTextAction()) // It's a TextField
            .performTextInput(" Jane")
        
        composeRule.onNodeWithText("John Jane").assertIsDisplayed()
    }
}
```

## 6. Compose UI Layer

```kotlin
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    
    UserScreenContent(
        state = state,
        onEvent = viewModel::onEvent
    )
}

@Composable
fun UserScreenContent(
    state: UserViewModel.UiState,
    onEvent: (UserViewModel.Event) -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("User Profile") },
                actions = {
                    if (state is UserViewModel.UiState.Success) {
                        IconButton(onClick = { onEvent(UserViewModel.Event.ToggleEdit) }) {
                            Icon(
                                if (state.isEditing) Icons.Default.Close else Icons.Default.Edit,
                                contentDescription = "Edit"
                            )
                        }
                    }
                }
            )
        }
    ) { padding ->
        Box(
            Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (state) {
                is UserViewModel.UiState.Loading -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                is UserViewModel.UiState.Error -> ErrorView(state.message) { onEvent(UserViewModel.Event.Retry) }
                is UserViewModel.UiState.Success -> UserForm(
                    user = state.user,
                    isEditing = state.isEditing,
                    onNameChange = { onEvent(UserViewModel.Event.UpdateName(it)) },
                    onEmailChange = { onEvent(UserViewModel.Event.UpdateEmail(it)) },
                    onSave = { onEvent(UserViewModel.Event.Save) }
                )
            }
        }
    }
}
```

## Architecture Benefits

| Layer | Responsibility | Test Coverage |
|-------|---------------|---------------|
| Domain | Business logic, models | Pure unit tests (no Android) |
| Data | API, DB, caching | Repository + DAO tests |
| Presentation | UI state, events | ViewModel + Compose UI tests |

## Key Patterns Summary

1. **Single source of truth** → Repository returns `Flow`, ViewModel holds `StateFlow`
2. **Unidirectional data flow** → Events up, State down
3. **Offline-first** → Cache in Room, emit + refresh
4. **Testable** → Interfaces everywhere, inject dispatchers
5. **Lifecycle-aware** → `collectAsStateWithLifecycle()`

---
*Learned: 2026-02-22 13:41 | Focus: MVVM architecture, Hilt DI, comprehensive testing patterns*