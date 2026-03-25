package com.terrarium.app.util

import com.terrarium.app.data.model.*

/**
 * Utility object for calculating plant-related stats and displaying plant information.
 */
object PlantCalculator {
    
    /**
     * Calculate time remaining for plant to reach maturity.
     */
    fun getTimeToMaturity(plant: Plant, plantType: PlantType): PlantTimeInfo {
        val hoursSincePlanting = TimeUtils.hoursSince(plant.plantedAt)
        val totalGrowthHours = plantType.growthTimeHours.toFloat()
        val remainingHours = maxOf(0, totalGrowthHours - hoursSincePlanting).toLong()
        
        val progressPercent = ((hoursSincePlanting / totalGrowthHours) * 100).coerceIn(0f, 100f)
        
        return PlantTimeInfo(
            hoursRemaining = remainingHours,
            progressPercent = progressPercent,
            growthStage = plant.growthStage
        )
    }
    
    /**
     * Get status message for a plant.
     */
    fun getStatusMessage(plant: Plant, plantType: PlantType): String {
        return when (plant.getStatus()) {
            PlantStatus.HEALTHY -> "Your ${plantType.name} is thriving! 🌿"
            PlantStatus.FAIR -> "Your ${plantType.name} is doing okay. Keep it watered!"
            PlantStatus.UNHEALTHY -> "Your ${plantType.name} needs attention!"
            PlantStatus.WILTING -> "Your ${plantType.name} is wilting! Water it now!"
            PlantStatus.OVERWATERED -> "Your ${plantType.name} is overwatered. Let it dry out."
            PlantStatus.DEAD -> "Your ${plantType.name} has died. 🥀"
        }
    }
    
    /**
     * Get moisture status.
     */
    fun getMoistureStatus(moisture: Float): MoistureStatus {
        return when {
            moisture > 0.95f -> MoistureStatus.OVERWATERED
            moisture > 0.8f -> MoistureStatus.HIGH
            moisture in 0.4f..0.8f -> MoistureStatus.OPTIMAL
            moisture in 0.25f..0.4f -> MoistureStatus.LOW
            moisture > 0.15f -> MoistureStatus.DRY
            else -> MoistureStatus.CRITICAL
        }
    }
    
    /**
     * Get health status.
     */
    fun getHealthStatus(health: Int): HealthStatus {
        return when {
            health >= 80 -> HealthStatus.EXCELLENT
            health >= 60 -> HealthStatus.GOOD
            health >= 40 -> HealthStatus.FAIR
            health >= 20 -> HealthStatus.POOR
            else -> HealthStatus.CRITICAL
        }
    }
    
    /**
     * Calculate optimal moisture range for a plant type.
     */
    fun getOptimalMoistureRange(plantType: PlantType): ClosedFloatingPointRange<Float> {
        return plantType.minMoisture..plantType.maxMoisture
    }
    
    /**
     * Check if moisture is in optimal range.
     */
    fun isMoistureOptimal(plant: Plant, plantType: PlantType): Boolean {
        return plant.moisture in getOptimalMoistureRange(plantType)
    }
    
    /**
     * Get water recommendation for a plant.
     */
    fun getWaterRecommendation(plant: Plant, plantType: PlantType): WaterRecommendation? {
        val status = getMoistureStatus(plant.moisture)
        val optimalRange = getOptimalMoistureRange(plantType)
        
        return when {
            plant.isDead -> WaterRecommendation(
                shouldWater = false,
                message = "This plant has died.",
                waterAmount = 0f
            )
            status == MoistureStatus.OVERWATERED -> WaterRecommendation(
                shouldWater = false,
                message = "Stop watering! Let it dry out.",
                waterAmount = 0f
            )
            status == MoistureStatus.CRITICAL -> WaterRecommendation(
                shouldWater = true,
                message = "Water immediately! Plant is critically dry.",
                waterAmount = GameLogic.calculateWaterAmount()
            )
            status == MoistureStatus.DRY -> WaterRecommendation(
                shouldWater = true,
                message = "Water soon. Plant needs moisture.",
                waterAmount = GameLogic.calculateWaterAmount()
            )
            status == MoistureStatus.LOW -> WaterRecommendation(
                shouldWater = true,
                message = "Consider watering to reach optimal levels.",
                waterAmount = GameLogic.calculateWaterAmount()
            )
            status == MoistureStatus.OPTIMAL -> WaterRecommendation(
                shouldWater = false,
                message = "Moisture levels are good. Check back later.",
                waterAmount = 0f
            )
            status == MoistureStatus.HIGH -> WaterRecommendation(
                shouldWater = false,
                message = "No need to water right now.",
                waterAmount = 0f
            )
            else -> null
        }
    }
}

data class PlantTimeInfo(
    val hoursRemaining: Long,
    val progressPercent: Float,
    val growthStage: GrowthStage
) {
    fun formatTimeRemaining(): String {
        return when {
            hoursRemaining < 1 -> "< 1 hour"
            hoursRemaining < 24 -> "${hoursRemaining}h"
            else -> "${hoursRemaining / 24}d ${hoursRemaining % 24}h"
        }
    }
}

enum class MoistureStatus {
    OVERWATERED,
    HIGH,
    OPTIMAL,
    LOW,
    DRY,
    CRITICAL
}

enum class HealthStatus {
    EXCELLENT,
    GOOD,
    FAIR,
    POOR,
    CRITICAL
}

data class WaterRecommendation(
    val shouldWater: Boolean,
    val message: String,
    val waterAmount: Float
)