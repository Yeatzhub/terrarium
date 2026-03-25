package com.terrarium.app.data.model
import kotlin.math.pow

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * User profile and progression data.
 */
@Entity(tableName = "users")
data class User(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String = "Gardener",
    val level: Int = 1,
    val xp: Long = 0,
    val coins: Int = 100,
    val lastLogin: Long = System.currentTimeMillis(),
    val dailyStreak: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val unlockedJarTypes: String = "SMALL", // Comma-separated list of unlocked JarTypes
    val dailyTasksCompleted: Int = 0,
    val totalPlantsGrown: Int = 0,
    val totalPropagations: Int = 0
) {
    /**
     * Calculate XP needed for next level.
     * Formula: 100 * level^1.5
     */
    fun xpToNextLevel(): Long {
        return (100 * level.toDouble().pow(1.5)).toLong()
    }
    
    /**
     * Check if user has enough XP to level up.
     */
    fun canLevelUp(): Boolean {
        return xp >= xpToNextLevel()
    }
    
    /**
     * Get list of unlocked jar types.
     */
    fun getUnlockedJarTypes(): List<JarType> {
        return if (unlockedJarTypes.isEmpty()) {
            listOf(JarType.SMALL)
        } else {
            unlockedJarTypes.split(",").mapNotNull { 
                try { JarType.valueOf(it.trim()) } catch (e: Exception) { null }
            }
        }
    }
    
    /**
     * Check if a jar type is unlocked.
     */
    fun hasJarUnlocked(jarType: JarType): Boolean {
        return getUnlockedJarTypes().contains(jarType)
    }
    
    /**
     * Get jars that unlock at specific levels.
     */
    fun getNewlyUnlockedJars(): List<JarType> {
        val unlocked = getUnlockedJarTypes().toMutableList()
        val newJars = mutableListOf<JarType>()
        
        // Level 3 unlocks Medium jar
        if (level >= 3 && !unlocked.contains(JarType.MEDIUM)) {
            newJars.add(JarType.MEDIUM)
        }
        // Level 7 unlocks Round and Tall jars
        if (level >= 7) {
            if (!unlocked.contains(JarType.ROUND)) newJars.add(JarType.ROUND)
            if (!unlocked.contains(JarType.TALL)) newJars.add(JarType.TALL)
        }
        // Level 12 unlocks Wide jar
        if (level >= 12 && !unlocked.contains(JarType.WIDE)) {
            newJars.add(JarType.WIDE)
        }
        
        return newJars
    }
    
    /**
     * Get XP progress as percentage (0-100).
     */
    fun getXpProgress(): Float {
        val needed = xpToNextLevel()
        return if (needed > 0) {
            ((xp.toFloat() / needed) * 100).coerceIn(0f, 100f)
        } else {
            100f
        }
    }
}

/**
 * Level unlock rewards.
 */
data class LevelReward(
    val level: Int,
    val jarUnlocks: List<JarType>,
    val coins: Int
)

object LevelRewards {
    val ALL = listOf(
        LevelReward(1, listOf(JarType.SMALL), 50),
        LevelReward(3, listOf(JarType.MEDIUM), 100),
        LevelReward(7, listOf(JarType.ROUND, JarType.TALL), 150),
        LevelReward(12, listOf(JarType.WIDE), 250)
    )
    
    fun getRewardForLevel(level: Int): LevelReward? {
        return ALL.find { it.level == level }
    }
}