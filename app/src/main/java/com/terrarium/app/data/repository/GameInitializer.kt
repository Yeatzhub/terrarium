package com.terrarium.app.data.repository

import com.terrarium.app.data.database.*
import com.terrarium.app.data.model.*
import com.terrarium.app.data.preferences.UserPreferences
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Handles first-time game initialization.
 * Creates user, default terrarium, and starter items.
 */
@Singleton
class GameInitializer @Inject constructor(
    private val userDao: UserDao,
    private val terrariumDao: TerrariumDao,
    private val plantDao: PlantDao,
    private val plantTypeDao: PlantTypeDao,
    private val inventoryDao: InventoryDao,
    private val dailyTaskRepository: DailyTaskRepository,
    private val userPreferences: UserPreferences
) {
    /**
     * Initialize game data for a new player.
     * Returns the user ID.
     */
    suspend fun initializeIfNeeded(): Long {
        // Check if user already exists
        val existingUser = userDao.getCurrentUser()
        if (existingUser != null) {
            return existingUser.id
        }
        
        // Create default user
        val userId = userDao.insertUser(
            User(
                name = "Gardener",
                level = 1,
                xp = 0,
                coins = 100, // Starting coins
                unlockedJarTypes = "SMALL"
            )
        )
        
        // Create default terrarium
        val terrariumId = terrariumDao.insertTerrarium(
            Terrarium(
                name = "My First Terrarium",
                jarType = JarType.SMALL,
                createdAt = System.currentTimeMillis()
            )
        )
        
        // Give starter seeds (5 Moss Seeds)
        inventoryDao.insertInventoryItem(
            InventoryItem(
                userId = userId,
                itemId = 1, // Moss Seeds
                itemType = ItemType.SEED,
                quantity = 5
            )
        )
        
        // Give additional starter seeds
        inventoryDao.insertInventoryItem(
            InventoryItem(
                userId = userId,
                itemId = 2, // Fittonia Seeds
                itemType = ItemType.SEED,
                quantity = 3
            )
        )
        
        // Initialize plant types if not exists
        initializePlantTypes()
        
        // Generate initial daily tasks
        dailyTaskRepository.generateDailyTasks(userId)
        
        return userId
    }
    
    /**
     * Update the first terrarium with base layers.
     */
    suspend fun updateBaseLayers(config: BaseLayerConfig) {
        val terrarium = terrariumDao.getAllTerrariums().first().firstOrNull()
        if (terrarium != null) {
            terrariumDao.updateTerrarium(
                terrarium.copy(
                    hasGravel = config.hasGravel,
                    hasCharcoal = config.hasCharcoal,
                    hasSoil = config.hasSoil,
                    hasMoss = config.hasMoss
                )
            )
        }
    }
    
    /**
     * Seed the database with plant type definitions.
     */
    private suspend fun initializePlantTypes() {
        // Check if plant types already exist
        if (plantTypeDao.getPlantTypeCount() > 0) {
            return
        }
        
        plantTypeDao.insertAll(DefaultPlantTypes.ALL)
    }
}