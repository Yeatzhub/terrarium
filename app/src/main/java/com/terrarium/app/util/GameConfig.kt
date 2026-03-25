package com.terrarium.app.util
import kotlin.math.pow

/**
 * Game constants and configuration values.
 */
object GameConfig {
    // Growth timing (in hours)
    const val COMMON_GROWTH_MIN = 4
    const val COMMON_GROWTH_MAX = 8
    const val UNCOMMON_GROWTH_MIN = 24
    const val UNCOMMON_GROWTH_MAX = 48
    const val RARE_GROWTH_MIN = 72
    const val RARE_GROWTH_MAX = 120
    const val LEGENDARY_GROWTH_MIN = 168
    const val LEGENDARY_GROWTH_MAX = 336
    
    // XP values
    const val XP_PER_WATER = 5
    const val XP_PER_PLANT = 20
    const val XP_PER_HARVEST = 50
    const val XP_PER_PROPAGATE = 20
    const val XP_PER_DAILY_LOGIN = 10
    const val XP_PER_DAILY_TASK_COMPLETED = 30
    
    // Coin values
    const val DAILY_BONUS_COINS = 25
    const val DAILY_BONUS_XP = 10
    const val STREAK_BONUS_COINS_MULTIPLIER = 5
    const val STREAK_BONUS_XP_MULTIPLIER = 5
    const val MAX_STREAK_BONUS_DAYS = 7
    
    // Plant health
    const val MAX_HEALTH = 100
    const val HEALTHY_THRESHOLD = 70
    const val FAIR_THRESHOLD = 50
    const val UNHEALTHY_THRESHOLD = 30
    const val WILTING_THRESHOLD = 20
    const val DEATH_THRESHOLD = 0
    const val DAYS_UNTIL_DEATH = 7
    const val HEALTH_DECAY_PER_DAY_NEGLECTED = 14
    
    // Moisture
    const val MIN_MOISTURE = 0f
    const val MAX_MOISTURE = 1f
    const val WATER_INCREASE_MIN = 0.15f
    const val WATER_INCREASE_MAX = 0.25f
    const val MOISTURE_DECAY_PER_HOUR = 0.02f
    const val OVERWATER_THRESHOLD = 0.95f
    const val LOW_MOISTURE_THRESHOLD = 0.30f
    const val DRY_THRESHOLD = 0.15f
    
    // Propagation
    const val CUTTING_MIN_HOURS = 48 // 2 days
    const val CUTTING_MAX_HOURS = 72 // 3 days
    const val PROPAGATION_SUCCESS_BASE = 0.75f
    
    // Level progression
    const val LEVEL_XP_BASE = 100
    const val LEVEL_XP_EXPONENT = 1.5
    
    // Jar unlocks
    const val JAR_MEDIUM_LEVEL = 3
    const val JAR_ROUND_LEVEL = 7
    const val JAR_TALL_LEVEL = 7
    const val JAR_WIDE_LEVEL = 12
    
    // Jar capacities
    const val JAR_SMALL_CAPACITY = 3
    const val JAR_MEDIUM_CAPACITY = 5
    const val JAR_ROUND_CAPACITY = 4
    const val JAR_TALL_CAPACITY = 6
    const val JAR_WIDE_CAPACITY = 7
    
    // Seed prices by tier
    const val COMMON_SEED_PRICE = 10
    const val UNCOMMON_SEED_PRICE = 50
    const val RARE_SEED_PRICE = 200
    const val LEGENDARY_SEED_PRICE = 1000
    
    // Tier level requirements
    const val COMMON_REQUIRED_LEVEL = 1
    const val UNCOMMON_REQUIRED_LEVEL = 3
    const val RARE_REQUIRED_LEVEL = 7
    const val LEGENDARY_REQUIRED_LEVEL = 12
    
    // Daily tasks
    const val DAILY_TASKS_COUNT = 4
    const val DAILY_TASK_RESET_HOUR = 0 // Midnight
    
    // Notifications
    const val MOISTURE_NOTIFICATION_THRESHOLD = 0.30f
    const val MOISTURE_CRITICAL_THRESHOLD = 0.15f
    
    // Background update intervals (in minutes)
    const val PLANT_UPDATE_INTERVAL_MINUTES = 60L
    
    // XP Level formula: level * 100^1.5
    fun xpForLevel(level: Int): Long {
        return (LEVEL_XP_BASE * level.toDouble().pow(LEVEL_XP_EXPONENT)).toLong()
    }
    
    fun getRequiredLevelForTier(tier: com.terrarium.app.data.model.RarityTier): Int {
        return when (tier) {
            com.terrarium.app.data.model.RarityTier.COMMON -> COMMON_REQUIRED_LEVEL
            com.terrarium.app.data.model.RarityTier.UNCOMMON -> UNCOMMON_REQUIRED_LEVEL
            com.terrarium.app.data.model.RarityTier.RARE -> RARE_REQUIRED_LEVEL
            com.terrarium.app.data.model.RarityTier.LEGENDARY -> LEGENDARY_REQUIRED_LEVEL
        }
    }
    
    fun getSeedPriceForTier(tier: com.terrarium.app.data.model.RarityTier): Int {
        return when (tier) {
            com.terrarium.app.data.model.RarityTier.COMMON -> COMMON_SEED_PRICE
            com.terrarium.app.data.model.RarityTier.UNCOMMON -> UNCOMMON_SEED_PRICE
            com.terrarium.app.data.model.RarityTier.RARE -> RARE_SEED_PRICE
            com.terrarium.app.data.model.RarityTier.LEGENDARY -> LEGENDARY_SEED_PRICE
        }
    }
}