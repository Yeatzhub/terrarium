package com.terrarium.app.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Represents a daily task for the user to complete.
 */
@Entity(tableName = "daily_tasks")
data class DailyTask(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val userId: Long,
    val name: String,
    val description: String,
    val xpReward: Int,
    val coinsReward: Int = 0,
    val isCompleted: Boolean = false,
    val taskType: TaskType,
    val targetCount: Int = 1, // How many times to complete (e.g., water 3 plants)
    val currentCount: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val expiresAt: Long = System.currentTimeMillis() + (24 * 60 * 60 * 1000) // 24 hours
)

/**
 * Types of daily tasks.
 */
enum class TaskType {
    WATER_PLANTS,
    PROPAGATE_PLANT,
    CHECK_TERRARIUM,
    BUY_ITEM,
    PLANT_SEED,
    HARVEST_PLANT,
    LOGIN,
    KEEP_PLANTS_HEALTHY
}

/**
 * Predefined daily task templates.
 */
object DailyTaskTemplates {
    val ALL = listOf(
        { DailyTaskTemplate("Thirsty Plants", "Water 3 plants", TaskType.WATER_PLANTS, 15, 10, 3) },
        { DailyTaskTemplate("Green Thumb", "Propagate a mature plant", TaskType.PROPAGATE_PLANT, 30, 25, 1) },
        { DailyTaskTemplate("Terrarium Check", "Check on your terrarium", TaskType.CHECK_TERRARIUM, 10, 5, 1) },
        { DailyTaskTemplate("Shop Browser", "Visit the shop", TaskType.BUY_ITEM, 10, 5, 1) },
        { DailyTaskTemplate("New Beginnings", "Plant a seed", TaskType.PLANT_SEED, 20, 15, 1) },
        { DailyTaskTemplate("Healthy Garden", "Keep all plants healthy above 70%", TaskType.KEEP_PLANTS_HEALTHY, 25, 20, 1) },
        { DailyTaskTemplate("Daily Login", "Log in today", TaskType.LOGIN, 10, 25, 1) }
    )
    
    fun getRandomTasks(count: Int = 4): List<DailyTaskTemplate> {
        return ALL.shuffled().take(count)
    }
}

data class DailyTaskTemplate(
    val name: String,
    val description: String,
    val taskType: TaskType,
    val xpReward: Int,
    val coinsReward: Int,
    val targetCount: Int
)