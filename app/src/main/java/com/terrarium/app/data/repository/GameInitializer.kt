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
    private val dailyTaskDao: DailyTaskDao,
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
        inventoryDao.insertItem(
            InventoryItem(
                userId = userId,
                itemId = 1, // Moss Seeds
                itemType = ItemType.SEED,
                quantity = 5
            )
        )
        
        // Give additional starter seeds
        inventoryDao.insertItem(
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
        dailyTaskDao.generateDailyTasks(userId)
        
        return userId
    }
    
    /**
     * Seed the database with plant type definitions.
     */
    private suspend fun initializePlantTypes() {
        // Check if plant types already exist
        if (plantTypeDao.getPlantTypeCount() > 0) {
            return
        }
        
        val plantTypes = listOf(
            // Common plants
            PlantType(1, "Moss", "Soft green carpet", PlantTier.COMMON, 4, 0.3f, 0.7f, 0.5f),
            PlantType(2, "Fittonia", "Nerve plant with colorful veins", PlantTier.COMMON, 6, 0.4f, 0.8f, 0.6f),
            PlantType(3, "Air Plant", "Tillandsia - no soil needed", PlantTier.COMMON, 5, 0.2f, 0.6f, 0.7f),
            PlantType(4, "Jade Plant", "Lucky succulent", PlantTier.COMMON, 8, 0.2f, 0.5f, 0.4f),
            // Uncommon plants
            PlantType(5, "Fern", "Classic terrarium fern", PlantTier.UNCOMMON, 12, 0.5f, 0.9f, 0.8f),
            PlantType(6, "Pilea", "Chinese money plant", PlantTier.UNCOMMON, 14, 0.4f, 0.7f, 0.6f),
            PlantType(7, "Peperomia", "Radiator plant", PlantTier.UNCOMMON, 10, 0.3f, 0.65f, 0.55f),
            PlantType(8, "String of Pearls", "Cascading succulent", PlantTier.UNCOMMON, 16, 0.2f, 0.4f, 0.3f),
            // Rare plants
            PlantType(9, "Variegated Pilea", "Rare variegated variety", PlantTier.RARE, 24, 0.35f, 0.7f, 0.65f),
            PlantType(10, "Pitcher Plant", "Carnivorous tropical", PlantTier.RARE, 36, 0.6f, 0.85f, 0.9f),
            PlantType(11, "Venus Flytrap", "Snap! Carnivorous", PlantTier.RARE, 48, 0.5f, 0.75f, 0.8f),
            // Legendary plants
            PlantType(12, "Ghost Plant", "Ethereal white beauty", PlantTier.LEGENDARY, 72, 0.4f, 0.6f, 0.7f),
            PlantType(13, "Living Stones", "Lithops - stone mimicry", PlantTier.LEGENDARY, 96, 0.15f, 0.3f, 0.25f),
            PlantType(14, "Marimo", "Aquatic moss sphere", PlantTier.LEGENDARY, 120, 0.8f, 1.0f, 0.95f),
            PlantType(15, "Moon Orchid", "Mythical blue orchid", PlantTier.LEGENDARY, 168, 0.45f, 0.75f, 0.7f)
        )
        
        plantTypeDao.insertAll(plantTypes)
    }
}