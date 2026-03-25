package com.terrarium.app.data.repository

import com.terrarium.app.data.database.PlantDao
import com.terrarium.app.data.model.GrowthStage
import com.terrarium.app.data.model.Plant
import com.terrarium.app.data.model.PlantType
import com.terrarium.app.util.GameLogic
import com.terrarium.app.util.TimeUtils
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PlantRepository @Inject constructor(
    private val plantDao: PlantDao
) {
    fun getPlantsForTerrarium(terrariumId: Long): Flow<List<Plant>> = 
        plantDao.getPlantsForTerrarium(terrariumId)
    
    suspend fun getPlantById(id: Long): Plant? = plantDao.getPlantById(id)
    
    suspend fun createPlant(plant: Plant): Long = plantDao.insertPlant(plant)
    
    suspend fun updatePlant(plant: Plant) = plantDao.updatePlant(plant)
    
    suspend fun deletePlant(plant: Plant) = plantDao.deletePlant(plant)
    
    /**
     * Water a plant - increases moisture and tracks timestamp.
     */
    suspend fun waterPlant(plant: Plant): Plant {
        val waterAmount = GameLogic.calculateWaterAmount()
        val newMoisture = minOf(1.0f, plant.moisture + waterAmount)
        
        val updatedPlant = plant.copy(
            moisture = newMoisture,
            lastWatered = System.currentTimeMillis(),
            daysNeglected = 0 // Reset neglect counter
        )
        
        plantDao.updatePlant(updatedPlant)
        return updatedPlant
    }
    
    /**
     * Update plant growth and health based on time passed.
     */
    suspend fun updatePlantStatus(plant: Plant, plantType: PlantType): Plant {
        val now = System.currentTimeMillis()
        val hoursSinceLastUpdate = TimeUtils.hoursSince(plant.lastGrowthUpdate)
        val hoursSinceWatered = TimeUtils.hoursSince(plant.lastWatered)
        
        // Calculate new moisture (decay over time)
        val newMoisture = GameLogic.calculateMoistureDecay(plant.moisture, hoursSinceWatered)
        
        // Update days neglected if plant is very dry
        val daysNeglected = if (newMoisture < GameLogic.DRY_THRESHOLD) {
            plant.daysNeglected + 1
        } else {
            plant.daysNeglected
        }
        
        // Check for overwatering
        val isOverwatered = newMoisture > GameLogic.OVERWATER_THRESHOLD
        
        // Calculate new health
        val tempPlant = plant.copy(
            moisture = newMoisture,
            daysNeglected = daysNeglected,
            isOverwatered = isOverwatered
        )
        val newHealth = GameLogic.calculateHealth(tempPlant, plantType)
        
        // Check for wilting
        val isWilting = newHealth < GameLogic.WILTING_THRESHOLD && newHealth > 0
        
        // Check for death
        val isDead = GameLogic.shouldDie(tempPlant) || newHealth <= 0
        
        // Update growth stage
        val newGrowthStage = if (!isDead) {
            GameLogic.calculateGrowthStage(plant, plantType)
        } else {
            plant.growthStage // Dead plants don't grow
        }
        
        val updatedPlant = plant.copy(
            moisture = newMoisture,
            health = newHealth,
            growthStage = newGrowthStage,
            daysNeglected = daysNeglected,
            isWilting = isWilting,
            isOverwatered = isOverwatered,
            isDead = isDead,
            lastGrowthUpdate = now
        )
        
        plantDao.updatePlant(updatedPlant)
        return updatedPlant
    }
    
    /**
     * Check if plant can be propagated.
     */
    fun canPropagate(plant: Plant): Boolean {
        return plant.canPropagate()
    }
    
    /**
     * Update all plants in a terrarium (called periodically).
     */
    suspend fun updateAllPlantsInTerrarium(
        terrariumId: Long, 
        plantTypes: Map<Long, PlantType>
    ): List<Plant> {
        val plants = plantDao.getPlantsForTerrarium(terrariumId)
        // Convert Flow to list first, then process each plant
        return mutableListOf<Plant>().apply {
            plants.collect { plantList ->
                for (plant in plantList) {
                    val plantType = plantTypes[plant.typeId]
                    if (plantType != null) {
                        updatePlantStatus(plant, plantType)
                    }
                }
            }
        }
    }
    
    /**
     * Get plants that need water notification.
     */
    fun getPlantsNeedingWater(plants: List<Plant>): List<Plant> {
        return plants.filter { GameLogic.needsWaterNotification(it) }
    }
}