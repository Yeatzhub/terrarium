package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.terrarium.app.util.TimeUtils

/**
 * Represents a plant growing in a terrarium.
 */
@Entity(
    tableName = "plants",
    foreignKeys = [
        ForeignKey(
            entity = Terrarium::class,
            parentColumns = ["id"],
            childColumns = ["terrariumId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("terrariumId"), Index("typeId")]
)
data class Plant(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val typeId: Long,
    val terrariumId: Long,
    val positionX: Float,
    val positionY: Float,
    val growthStage: GrowthStage = GrowthStage.SEED,
    val health: Int = 100,
    val moisture: Float = 0.5f,
    val light: Float = 0.5f, // Light level in terrarium (0-1)
    val humidity: Float = 0.6f, // Humidity level (0-1)
    val lastWatered: Long = System.currentTimeMillis(),
    val lastChecked: Long = System.currentTimeMillis(),
    val plantedAt: Long = System.currentTimeMillis(),
    val lastGrowthUpdate: Long = System.currentTimeMillis(),
    val isWilting: Boolean = false,
    val isDead: Boolean = false,
    val isOverwatered: Boolean = false,
    val daysNeglected: Int = 0
) {
    /**
     * Calculate current health based on moisture, light, and humidity levels.
     */
    fun calculateHealth(plantType: PlantType): Int {
        var healthScore = 100
        
        // Moisture factor - check if within optimal range
        val moisturePenalty = if (moisture < plantType.minMoisture) {
            (plantType.minMoisture - moisture) * 100 // Underwatered penalty
        } else if (moisture > plantType.maxMoisture) {
            (moisture - plantType.maxMoisture) * 100 // Overwatered penalty
        } else {
            0f
        }
        healthScore -= moisturePenalty.toInt().coerceIn(0, 50)
        
        // Light factor
        val lightPenalty = if (light < plantType.minLight) {
            (plantType.minLight - light) * 80
        } else if (light > plantType.maxLight) {
            (light - plantType.maxLight) * 40
        } else {
            0f
        }
        healthScore -= lightPenalty.toInt().coerceIn(0, 30)
        
        // Humidity factor
        val humidityPenalty = if (moisture > 0.3f) { // Only matters when watered
            if (humidity < 0.4f) 15 else 0 // Low humidity stress
        } else 0
        healthScore -= humidityPenalty
        
        // Neglect penalty - health drops over time if ignored
        healthScore -= (daysNeglected * 10).coerceIn(0, 70)
        
        return healthScore.coerceIn(0, 100)
    }
    
    /**
     * Check if plant is ready to progress to next growth stage.
     */
    fun canProgressToNextStage(plantType: PlantType): Boolean {
        if (growthStage == GrowthStage.MATURE) return false
        
        val hoursElapsed = TimeUtils.hoursSince(lastGrowthUpdate)
        return hoursElapsed >= plantType.growthTimeHours && health >= 50
    }
    
    /**
     * Get growth progress percentage (0-100).
     */
    fun getGrowthProgress(plantType: PlantType): Float {
        val hoursElapsed = TimeUtils.hoursSince(lastGrowthUpdate)
        return ((hoursElapsed.toFloat() / plantType.growthTimeHours) * 100).coerceIn(0f, 100f)
    }
    
    /**
     * Check if plant is mature and can be propagated.
     */
    fun canPropagate(): Boolean {
        return growthStage == GrowthStage.MATURE && health >= 70 && !isDead && !isWilting
    }
    
    /**
     * Get time until next growth stage in hours.
     */
    fun timeToNextStage(plantType: PlantType): Long {
        val hoursElapsed = TimeUtils.hoursSince(lastGrowthUpdate)
        return maxOf(0, plantType.growthTimeHours - hoursElapsed)
    }
    
    /**
     * Get plant status for display.
     */
    fun getStatus(): PlantStatus {
        return when {
            isDead -> PlantStatus.DEAD
            isOverwatered -> PlantStatus.OVERWATERED
            isWilting -> PlantStatus.WILTING
            health < 30 -> PlantStatus.UNHEALTHY
            health < 70 -> PlantStatus.FAIR
            else -> PlantStatus.HEALTHY
        }
    }
}

/**
 * Growth stages for plants.
 */
enum class GrowthStage {
    SEED,
    SPROUT,
    YOUNG,
    MATURE
}

/**
 * Plant health status for display.
 */
enum class PlantStatus {
    HEALTHY,
    FAIR,
    UNHEALTHY,
    WILTING,
    OVERWATERED,
    DEAD;
    
    fun getEmoji(): String = when (this) {
        HEALTHY -> "🌿"
        FAIR -> "🌱"
        UNHEALTHY -> "🥀"
        WILTING -> "😔"
        OVERWATERED -> "💧"
        DEAD -> "☠️"
    }
    
    fun getDisplayName(): String = when (this) {
        HEALTHY -> "Healthy"
        FAIR -> "Fair"
        UNHEALTHY -> "Unhealthy"
        WILTING -> "Wilting"
        OVERWATERED -> "Overwatered"
        DEAD -> "Dead"
    }
}