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
    val lastVisited: Long = System.currentTimeMillis()
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