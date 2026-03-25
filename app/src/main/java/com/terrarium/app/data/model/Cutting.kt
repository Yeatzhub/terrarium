package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey
import com.terrarium.app.util.TimeUtils

/**
 * Represents a plant cutting that needs time to root before planting.
 */
@Entity(
    tableName = "cuttings",
    foreignKeys = [
        ForeignKey(
            entity = PlantType::class,
            parentColumns = ["id"],
            childColumns = ["typeId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("typeId"), Index("userId")]
)
data class Cutting(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: Long,
    val typeId: Long,
    val sourcePlantId: Long, // The plant this came from
    val createdAt: Long = System.currentTimeMillis(),
    val readyAt: Long, // When it can be planted
    val isReady: Boolean = false
) {
    /**
     * Check if cutting is ready to plant.
     */
    fun isReadyToPlant(): Boolean {
        return System.currentTimeMillis() >= readyAt
    }
    
    /**
     * Get remaining time until ready (in hours).
     */
    fun hoursUntilReady(): Long {
        return maxOf(0, TimeUtils.hoursSince(readyAt))
    }
    
    /**
     * Get progress towards being ready (0-100).
     */
    fun getProgress(): Float {
        val totalTime = readyAt - createdAt
        val elapsed = System.currentTimeMillis() - createdAt
        return ((elapsed.toFloat() / totalTime) * 100).coerceIn(0f, 100f)
    }
    
    companion object {
        /**
         * Create a new cutting from a plant.
         * Cuttings take 2-3 days to root.
         */
        fun createFromPlant(userId: Long, plantId: Long, plantTypeId: Long): Cutting {
            val readyDelayHours = (2..3).random().toLong()
            val readyAt = System.currentTimeMillis() + (readyDelayHours * 60 * 60 * 1000)
            return Cutting(
                userId = userId,
                typeId = plantTypeId,
                sourcePlantId = plantId,
                readyAt = readyAt
            )
        }
    }
}