package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Represents a terrarium container owned by the user.
 */
@Entity(tableName = "terrariums")
data class Terrarium(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val jarType: JarType,
    val createdAt: Long = System.currentTimeMillis(),
    val level: Int = 1,
    val name: String = "My Terrarium",
    val humidity: Float = 0.6f, // Humidity level (0-1)
    val light: Float = 0.5f, // Light level (0-1)
    val lastVisited: Long = System.currentTimeMillis(),
    // Base layers
    val hasGravel: Boolean = false,
    val hasCharcoal: Boolean = false,
    val hasSoil: Boolean = false,
    val hasMoss: Boolean = false,
    // Stats
    val totalPlantsGrown: Int = 0,
    val totalPropagations: Int = 0
) {
    /**
     * Get maximum plant capacity for this jar type.
     */
    fun getCapacity(): Int {
        return when (jarType) {
            JarType.SMALL -> 3
            JarType.MEDIUM -> 5
            JarType.ROUND -> 4
            JarType.WIDE -> 7
            JarType.TALL -> 6
        }
    }
    
    /**
     * Check if terrarium can hold more plants.
     */
    fun canAddPlants(plantCount: Int): Boolean {
        return plantCount < getCapacity()
    }
    
    /**
     * Check if terrarium has base layers set up.
     */
    fun hasBaseLayers(): Boolean {
        return hasSoil // Minimum requirement
    }
    
    /**
     * Get base layer configuration.
     */
    fun getBaseLayerConfig(): BaseLayerConfig {
        return BaseLayerConfig(
            hasGravel = hasGravel,
            hasCharcoal = hasCharcoal,
            hasSoil = hasSoil,
            hasMoss = hasMoss
        )
    }
    
    /**
     * Get total depth of base layers for rendering.
     */
    fun getLayerDepth(): Float {
        return getBaseLayerConfig().getTotalDepth()
    }
    
    /**
     * Get XP bonus for complete setup.
     */
    fun getSetupBonus(): Int {
        return getBaseLayerConfig().getSetupBonus()
    }
}

/**
 * Types of terrarium jars available.
 */
enum class JarType {
    SMALL,
    MEDIUM,
    ROUND,
    WIDE,
    TALL
}