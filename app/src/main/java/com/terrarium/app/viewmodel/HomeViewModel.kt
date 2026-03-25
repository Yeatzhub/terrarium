package com.terrarium.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.terrarium.app.data.model.*
import com.terrarium.app.data.repository.*
import com.terrarium.app.util.GameLogic
import com.terrarium.app.util.TimeUtils
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val terrariumRepository: TerrariumRepository,
    private val plantRepository: PlantRepository,
    private val plantTypeRepository: PlantTypeRepository,
    private val userRepository: UserRepository,
    private val inventoryRepository: InventoryRepository,
    private val dailyTaskRepository: DailyTaskRepository,
    private val cuttingRepository: CuttingRepository
) : ViewModel() {
    
    private val _selectedTerrariumId = MutableStateFlow<Long?>(null)
    private val _userId = MutableStateFlow(1L)
    private val _isLoading = MutableStateFlow(false)
    private val _message = MutableStateFlow<String?>(null)
    
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    val message: StateFlow<String?> = _message.asStateFlow()
    
    val user: StateFlow<User?> = _userId
        .flatMapLatest { userId ->
            flow { emit(userRepository.getUserById(userId)) }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, null)
    
    val terrariums: StateFlow<List<Terrarium>> = terrariumRepository.getAllTerrariums()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val selectedTerrarium: StateFlow<Terrarium?> = _selectedTerrariumId
        .flatMapLatest { id ->
            if (id == null) {
                flowOf(null)
            } else {
                flow { emit(terrariumRepository.getTerrariumById(id)) }
            }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, null)
    
    val plants: StateFlow<List<Plant>> = _selectedTerrariumId
        .flatMapLatest { id ->
            if (id == null) {
                flowOf(emptyList())
            } else {
                plantRepository.getPlantsForTerrarium(id)
            }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val plantTypes: StateFlow<List<PlantType>> = plantTypeRepository.getAllPlantTypes()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val dailyTasks: StateFlow<List<DailyTask>> = _userId
        .flatMapLatest { userId ->
            dailyTaskRepository.getActiveTasksForUser(userId)
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val cuttings: StateFlow<List<Cutting>> = _userId
        .flatMapLatest { userId ->
            cuttingRepository.getCuttingsForUser(userId)
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val inventory: StateFlow<List<InventoryItem>> = _userId
        .flatMapLatest { userId ->
            inventoryRepository.getInventoryForUser(userId)
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    // Computed properties
    val plantsNeedingWater: StateFlow<List<Plant>> = plants
        .map { plantList -> plantList.filter { GameLogic.needsWaterNotification(it) } }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val totalXpProgress: StateFlow<Float> = user
        .map { u -> u?.getXpProgress() ?: 0f }
        .stateIn(viewModelScope, SharingStarted.Lazily, 0f)
    
    init {
        // Initialize data
        viewModelScope.launch {
            // Get current user
            userRepository.getCurrentUser()?.let { u ->
                _userId.value = u.id
                
                // Check for daily login
                val loginResult = userRepository.recordDailyLogin(u.id)
                if (loginResult.wasNewLogin) {
                    _message.value = "Daily login bonus: +${loginResult.coinsGained} coins, +${loginResult.xpGained} XP!"
                    
                    // Generate daily tasks if needed
                    dailyTaskRepository.generateDailyTasks(u.id)
                }
            }
            
            // Select the first terrarium by default
            terrariums.firstOrNull { it.isNotEmpty() }?.firstOrNull()?.let {
                _selectedTerrariumId.value = it.id
            }
        }
    }
    
    fun selectTerrarium(id: Long) {
        _selectedTerrariumId.value = id
    }
    
    /**
     * Water a specific plant.
     */
    fun waterPlant(plantId: Long) {
        viewModelScope.launch {
            _isLoading.value = true
            
            plantRepository.getPlantById(plantId)?.let { plant ->
                val plantType = plantTypes.value.find { it.id == plant.typeId }
                if (plantType != null) {
                    // Water the plant
                    val updatedPlant = plantRepository.waterPlant(plant)
                    
                    // Add XP
                    userRepository.addXp(_userId.value, GameLogic.XP_WATER_PLANT.toLong())
                    
                    // Update daily task progress
                    dailyTaskRepository.updateTaskProgress(_userId.value, TaskType.WATER_PLANTS)
                    
                    _message.value = "Watered plant! Moisture: ${(updatedPlant.moisture * 100).toInt()}%"
                }
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Water all plants in the selected terrarium.
     */
    fun waterAllPlants() {
        viewModelScope.launch {
            _isLoading.value = true
            
            val terrariumId = _selectedTerrariumId.value ?: return@launch
            val plantList = plantRepository.getPlantsForTerrarium(terrariumId).first()
            var xpGained = 0L
            
            plantList.forEach { plant ->
                if (!plant.isDead) {
                    plantRepository.waterPlant(plant)
                    xpGained += GameLogic.XP_WATER_PLANT
                }
            }
            
            if (xpGained > 0) {
                userRepository.addXp(_userId.value, xpGained)
                userRepository.recordDailyLogin(_userId.value)
                dailyTaskRepository.updateTaskProgress(_userId.value, TaskType.WATER_PLANTS)
                _message.value = "Watered ${plantList.size} plants! +$xpGained XP"
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Propagate a mature plant to create a cutting.
     */
    fun propagatePlant(plantId: Long) {
        viewModelScope.launch {
            _isLoading.value = true
            
            plantRepository.getPlantById(plantId)?.let { plant ->
                val plantType = plantTypes.value.find { it.id == plant.typeId }
                
                if (plant.canPropagate()) {
                    // Check propagation success
                    val successChance = GameLogic.getPropagationSuccessChance(plant)
                    val success = Math.random() < successChance
                    
                    if (success) {
                        // Create cutting
                        val cutting = Cutting.createFromPlant(_userId.value, plant.id, plant.typeId)
                        cuttingRepository.createCutting(cutting)
                        
                        // Add XP
                        userRepository.addXp(_userId.value, GameLogic.XP_PROPAGATE_PLANT.toLong())
                        
                        // Update task progress
                        dailyTaskRepository.updateTaskProgress(_userId.value, TaskType.PROPAGATE_PLANT)
                        
                        _message.value = "Successfully propagated ${plantType?.name ?: "plant"}! Cutting will be ready in 2-3 days."
                    } else {
                        _message.value = "Propagation failed. Try again with a healthier plant!"
                    }
                } else {
                    _message.value = "This plant cannot be propagated yet. Wait until it's mature and healthy."
                }
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Plant a seed from inventory.
     */
    fun plantSeed(plantTypeId: Long, terrariumId: Long, positionX: Float, positionY: Float) {
        viewModelScope.launch {
            _isLoading.value = true
            
            val userId = _userId.value
            
            // Check if user has the seed
            val hasSeed = inventoryRepository.hasItem(userId, plantTypeId, ItemType.SEED)
            
            if (hasSeed) {
                // Create the plant
                val plant = Plant(
                    typeId = plantTypeId,
                    terrariumId = terrariumId,
                    positionX = positionX,
                    positionY = positionY,
                    growthStage = GrowthStage.SEED,
                    health = 100,
                    moisture = 0.5f,
                    plantedAt = System.currentTimeMillis()
                )
                
                plantRepository.createPlant(plant)
                
                // Remove seed from inventory
                inventoryRepository.removeInventoryItem(userId, plantTypeId, ItemType.SEED)
                
                // Add XP
                userRepository.addXp(userId, GameLogic.XP_PLANT_SEED.toLong())
                
                // Update task progress
                dailyTaskRepository.updateTaskProgress(userId, TaskType.PLANT_SEED)
                
                _message.value = "Seed planted! Check back in a few hours to see it grow."
            } else {
                _message.value = "You don't have any seeds of this type."
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Create a new terrarium.
     */
    fun createTerrarium(name: String, jarType: JarType) {
        viewModelScope.launch {
            val user = userRepository.getUserById(_userId.value)
            
            if (user != null && user.hasJarUnlocked(jarType)) {
                val terrariumId = terrariumRepository.createTerrarium(
                    Terrarium(name = name, jarType = jarType)
                )
                _selectedTerrariumId.value = terrariumId
                _message.value = "Created new terrarium: $name"
            } else {
                _message.value = "You haven't unlocked this jar type yet!"
            }
        }
    }
    
    /**
     * Clear the message.
     */
    fun clearMessage() {
        _message.value = null
    }
    
    /**
     * Get plant type by ID.
     */
    fun getPlantType(typeId: Long): PlantType? {
        return plantTypes.value.find { it.id == typeId }
    }
    
    /**
     * Refresh all plant statuses.
     */
    fun refreshPlantStatuses() {
        viewModelScope.launch {
            val terrariumId = _selectedTerrariumId.value ?: return@launch
            val plantList = plants.value
            val plantTypeMap = plantTypes.value.associateBy { it.id }
            
            plantList.forEach { plant ->
                val plantType = plantTypeMap[plant.typeId]
                if (plantType != null) {
                    plantRepository.updatePlantStatus(plant, plantType)
                }
            }
        }
    }
    
    /**
     * Complete a daily task (mark as completed).
     */
    fun completeTask(taskId: Long) {
        viewModelScope.launch {
            dailyTaskRepository.getTaskById(taskId)?.let { task ->
                if (!task.isCompleted) {
                    val updatedTask = task.copy(
                        currentCount = task.targetCount,
                        isCompleted = true
                    )
                    dailyTaskRepository.updateTask(updatedTask)
                    
                    // Award XP and coins
                    userRepository.addXp(_userId.value, task.xpReward.toLong())
                    userRepository.addCoins(_userId.value, task.coinsReward ?: 0)
                    
                    _message.value = "Task completed! +${task.xpReward} XP, +${task.coinsReward} coins"
                }
            }
        }
    }
}