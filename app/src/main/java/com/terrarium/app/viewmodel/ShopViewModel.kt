package com.terrarium.app.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.terrarium.app.data.model.*
import com.terrarium.app.data.repository.InventoryRepository
import com.terrarium.app.data.repository.PlantTypeRepository
import com.terrarium.app.data.repository.UserRepository
import com.terrarium.app.util.GameLogic
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ShopViewModel @Inject constructor(
    private val plantTypeRepository: PlantTypeRepository,
    private val inventoryRepository: InventoryRepository,
    private val userRepository: UserRepository
) : ViewModel() {
    
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
    
    val allPlantTypes: StateFlow<List<PlantType>> = plantTypeRepository.getAllPlantTypes()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val commonPlants: StateFlow<List<PlantType>> = plantTypeRepository.getPlantTypesByTier(RarityTier.COMMON)
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val uncommonPlants: StateFlow<List<PlantType>> = plantTypeRepository.getPlantTypesByTier(RarityTier.UNCOMMON)
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val rarePlants: StateFlow<List<PlantType>> = plantTypeRepository.getPlantTypesByTier(RarityTier.RARE)
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val legendaryPlants: StateFlow<List<PlantType>> = plantTypeRepository.getPlantTypesByTier(RarityTier.LEGENDARY)
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    val inventory: StateFlow<List<InventoryItem>> = _userId
        .flatMapLatest { userId ->
            inventoryRepository.getInventoryForUser(userId)
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    // Seed shop items
    val seedShopItems: StateFlow<List<ShopItem>> = flow {
        // Convert ShopItems.SEEDS to actual items
        emit(ShopItems.SEEDS)
    }.stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    // Jar shop items
    val jarShopItems: StateFlow<List<ShopItem>> = flow {
        emit(ShopItems.JARS)
    }.stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    // Decoration shop items
    val decorationShopItems: StateFlow<List<ShopItem>> = flow {
        emit(ShopItems.DECORATIONS)
    }.stateIn(viewModelScope, SharingStarted.Lazily, emptyList())
    
    init {
        // Get current user
        viewModelScope.launch {
            userRepository.getCurrentUser()?.let { u ->
                _userId.value = u.id
            }
        }
    }
    
    // Seed packet prices by tier
    fun getPriceForTier(tier: RarityTier): Int = GameLogic.getSeedPrice(tier)
    
    /**
     * Purchase a seed.
     */
    fun purchaseSeed(plantType: PlantType) {
        viewModelScope.launch {
            _isLoading.value = true
            
            val userId = _userId.value
            val price = getPriceForTier(plantType.tier)
            
            // Check if user has enough coins and level
            val currentUser = userRepository.getUserById(userId)
            if (currentUser == null) {
                _message.value = "Error: User not found"
                _isLoading.value = false
                return@launch
            }
            
            if (currentUser.coins < price) {
                _message.value = "Not enough coins! Need $price coins."
                _isLoading.value = false
                return@launch
            }
            
            if (currentUser.level < getRequiredLevelForTier(plantType.tier)) {
                _message.value = "You need to reach level ${getRequiredLevelForTier(plantType.tier)} to buy this seed!"
                _isLoading.value = false
                return@launch
            }
            
            // Deduct coins
            val success = userRepository.deductCoins(userId, price)
            if (success) {
                // Add seed to inventory
                inventoryRepository.addInventoryItem(userId, plantType.id, ItemType.SEED)
                _message.value = "Purchased ${plantType.name} seed for $price coins!"
            } else {
                _message.value = "Purchase failed. Please try again."
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Purchase a jar unlock.
     */
    fun purchaseJar(jarItem: ShopItem) {
        viewModelScope.launch {
            _isLoading.value = true
            
            val userId = _userId.value
            val currentUser = userRepository.getUserById(userId)
            
            if (currentUser == null) {
                _message.value = "Error: User not found"
                _isLoading.value = false
                return@launch
            }
            
            // Check level requirement
            val jarType = when (jarItem.id) {
                102L -> JarType.MEDIUM
                103L -> JarType.ROUND
                104L -> JarType.TALL
                105L -> JarType.WIDE
                else -> JarType.SMALL
            }
            
            val requiredLevel = GameLogic.getJarUnlockLevel(jarType)
            if (currentUser.level < requiredLevel) {
                _message.value = "You need to reach level $requiredLevel to unlock this jar!"
                _isLoading.value = false
                return@launch
            }
            
            // Check if already unlocked
            if (currentUser.hasJarUnlocked(jarType)) {
                _message.value = "You already have this jar unlocked!"
                _isLoading.value = false
                return@launch
            }
            
            // Check coins
            if (currentUser.coins < jarItem.price) {
                _message.value = "Not enough coins! Need ${jarItem.price} coins."
                _isLoading.value = false
                return@launch
            }
            
            // Deduct coins
            val success = userRepository.deductCoins(userId, jarItem.price)
            if (success) {
                // Add jar unlock to inventory
                inventoryRepository.addInventoryItem(userId, jarItem.id, ItemType.JAR_UNLOCK)
                _message.value = "Purchased ${jarItem.name} for ${jarItem.price} coins!"
            } else {
                _message.value = "Purchase failed. Please try again."
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Purchase a decoration.
     */
    fun purchaseDecoration(decorationItem: ShopItem) {
        viewModelScope.launch {
            _isLoading.value = true
            
            val userId = _userId.value
            val currentUser = userRepository.getUserById(userId)
            
            if (currentUser == null) {
                _message.value = "Error: User not found"
                _isLoading.value = false
                return@launch
            }
            
            // Check level requirement
            if (currentUser.level < decorationItem.requiredLevel) {
                _message.value = "You need to reach level ${decorationItem.requiredLevel} to buy this item!"
                _isLoading.value = false
                return@launch
            }
            
            // Check coins
            if (currentUser.coins < decorationItem.price) {
                _message.value = "Not enough coins! Need ${decorationItem.price} coins."
                _isLoading.value = false
                return@launch
            }
            
            // Deduct coins
            val success = userRepository.deductCoins(userId, decorationItem.price)
            if (success) {
                // Add decoration to inventory
                inventoryRepository.addInventoryItem(userId, decorationItem.id, ItemType.DECORATION)
                _message.value = "Purchased ${decorationItem.name} for ${decorationItem.price} coins!"
            } else {
                _message.value = "Purchase failed. Please try again."
            }
            
            _isLoading.value = false
        }
    }
    
    /**
     * Check if user can afford an item.
     */
    fun canAfford(price: Int): Boolean {
        val currentUser = user.value ?: return false
        return currentUser.coins >= price
    }
    
    /**
     * Check if user has required level for an item.
     */
    fun hasRequiredLevel(requiredLevel: Int): Boolean {
        val currentUser = user.value ?: return false
        return currentUser.level >= requiredLevel
    }
    
    /**
     * Clear the message.
     */
    fun clearMessage() {
        _message.value = null
    }
    
    private fun getRequiredLevelForTier(tier: RarityTier): Int {
        return when (tier) {
            RarityTier.COMMON -> 1
            RarityTier.UNCOMMON -> 3
            RarityTier.RARE -> 7
            RarityTier.LEGENDARY -> 12
        }
    }
}