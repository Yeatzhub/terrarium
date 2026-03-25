package com.terrarium.app.util

import com.terrarium.app.data.model.*
import kotlin.math.pow
import kotlin.math.roundToInt

/**
 * Central game logic for Terrarium.
 * Handles growth calculations, health updates, and game mechanics.
 */
object GameLogic {
    
    // Growth timing multipliers
    private const val GROWTH_STAGE_HOURS = 0.25 // Each stage takes 25% of total growth time
    
    // Health thresholds
    const val HEALTHY_THRESHOLD = 70
    const val FAIR_THRESHOLD = 50
    const val UNHEALTHY_THRESHOLD = 30
    const val WILTING_THRESHOLD = 20
    const val DEATH_THRESHOLD = 0
    
    // Moisture settings
    const val WATER_INCREASE_MIN = 0.15f
    const val WATER_INCREASE_MAX = 0.25f
    const val MOISTURE_DECAY_PER_HOUR = 0.02f
    const val OVERWATER_THRESHOLD = 0.95f
    const val LOW_MOISTURE_THRESHOLD = 0.30f
    const val DRY_THRESHOLD = 0.15f
    
    // Neglect settings
    const val MAX_DAYS_NEGLECTED = 7
    const val HEALTH_DECAY_PER_DAY_NEGLECTED = 14 // ~2 health per day if ignored
    const val HEALTH_DECAY_PER_HOUR_OVERWATERED = 2
    
    // XP rewards
    const val XP_WATER_PLANT = 5
    const val XP_PROPAGATE_PLANT = 20
    const val XP_DAILY_LOGIN = 10
    const val XP_PLANT_SEED = 15
    const val XP_HARVEST_PLANT = 50
    const val XP_COMPLETE_ALL_DAILY_TASKS = 30
    
    // Coin rewards
    const val COINS_DAILY_LOGIN_BONUS = 25
    const val COINS_STREAK_BONUS_MULTIPLIER = 5
    
    /**
     * Calculate the current growth stage based on time elapsed.
     */
    fun calculateGrowthStage(plant: Plant, plantType: PlantType): GrowthStage {
        val hoursElapsed = TimeUtils.hoursSince(plant.plantedAt)
        val totalGrowthHours = plantType.growthTimeHours.toFloat()
        
        val progress = hoursElapsed / totalGrowthHours
        
        return when {
            progress >= 1.0f -> GrowthStage.MATURE
            progress >= 0.75f -> GrowthStage.YOUNG
            progress >= 0.50f -> GrowthStage.SPROUT
            else -> GrowthStage.SEED
        }
    }
    
    /**
     * Calculate plant health based on current conditions.
     */
    fun calculateHealth(plant: Plant, plantType: PlantType): Int {
        var health = 100
        
        // Moisture penalty
        when {
            plant.moisture > OVERWATER_THRESHOLD -> {
                // Overwatered - significant penalty and risk of rot
                health -= 30
            }
            plant.moisture < DRY_THRESHOLD -> {
                // Extremely dry - severe penalty
                health -= 40
            }
            plant.moisture < plantType.minMoisture -> {
                // Underwatered
                val deficit = plantType.minMoisture - plant.moisture
                health -= (deficit * 100).roundToInt()
            }
            plant.moisture > plantType.maxMoisture -> {
                // Slightly overwatered
                val excess = plant.moisture - plantType.maxMoisture
                health -= (excess * 50).roundToInt()
            }
        }
        
        // Light penalty (if outside optimal range)
        if (plant.light < plantType.minLight) {
            val deficit = plantType.minLight - plant.light
            health -= (deficit * 60).roundToInt()
        } else if (plant.light > plantType.maxLight) {
            val excess = plant.light - plantType.maxLight
            health -= (excess * 30).roundToInt()
        }
        
        // Neglect penalty
        health -= plant.daysNeglected * HEALTH_DECAY_PER_DAY_NEGLECTED
        
        // Health cannot go below 0
        return health.coerceIn(0, 100)
    }
    
    /**
     * Update plant moisture level (decay over time).
     */
    fun calculateMoistureDecay(currentMoisture: Float, hoursSinceWatered: Long): Float {
        val decay = hoursSinceWatered * MOISTURE_DECAY_PER_HOUR
        return (currentMoisture - decay).coerceIn(0f, 1f)
    }
    
    /**
     * Calculate water amount (random between min and max).
     */
    fun calculateWaterAmount(): Float {
        return WATER_INCREASE_MIN + (Math.random() * (WATER_INCREASE_MAX - WATER_INCREASE_MIN)).toFloat()
    }
    
    /**
     * Check if a plant is wilting.
     */
    fun isWilting(plant: Plant, plantType: PlantType): Boolean {
        val health = calculateHealth(plant, plantType)
        return health < WILTING_THRESHOLD && health > DEATH_THRESHOLD
    }
    
    /**
     * Check if a plant should die.
     */
    fun shouldDie(plant: Plant): Boolean {
        return plant.daysNeglected >= MAX_DAYS_NEGLECTED
    }
    
    /**
     * Check if a plant is overwatered.
     */
    fun isOverwatered(plant: Plant): Boolean {
        return plant.moisture > OVERWATER_THRESHOLD
    }
    
    /**
     * Check if plant needs water notification.
     */
    fun needsWaterNotification(plant: Plant): Boolean {
        return plant.moisture < LOW_MOISTURE_THRESHOLD && !plant.isDead
    }
    
    /**
     * Get XP required for a specific level.
     * Formula: 100 * level^1.5
     */
    fun xpForLevel(level: Int): Long {
        return (100 * level.toDouble().pow(1.5)).toLong()
    }
    
    /**
     * Calculate total XP needed from level 1 to target level.
     */
    fun totalXpForLevel(level: Int): Long {
        var total = 0L
        for (l in 1 until level) {
            total += xpForLevel(l)
        }
        return total
    }
    
    /**
     * Determine what level a user should be at based on total XP.
     */
    fun levelFromXp(totalXp: Long): Int {
        var xp = totalXp
        var level = 1
        var xpNeeded = xpForLevel(1)
        
        while (xp >= xpNeeded && level < 100) {
            xp -= xpNeeded
            level++
            xpNeeded = xpForLevel(level)
        }
        
        return level
    }
    
    /**
     * Calculate coins for daily login with streak bonus.
     */
    fun calculateDailyLoginCoins(streak: Int): Int {
        val streakBonus = minOf(streak, 7) * COINS_STREAK_BONUS_MULTIPLIER
        return COINS_DAILY_LOGIN_BONUS + streakBonus
    }
    
    /**
     * Calculate coins for daily login XP.
     */
    fun calculateDailyLoginXp(streak: Int): Int {
        val streakBonus = minOf(streak, 7) * 5
        return XP_DAILY_LOGIN + streakBonus
    }
    
    /**
     * Get jar capacity based on type.
     */
    fun getJarCapacity(jarType: JarType): Int {
        return when (jarType) {
            JarType.SMALL -> 3
            JarType.MEDIUM -> 5
            JarType.ROUND -> 4
            JarType.WIDE -> 7
            JarType.TALL -> 6
        }
    }
    
    /**
     * Get jar unlock level required.
     */
    fun getJarUnlockLevel(jarType: JarType): Int {
        return when (jarType) {
            JarType.SMALL -> 1
            JarType.MEDIUM -> 3
            JarType.ROUND -> 7
            JarType.TALL -> 7
            JarType.WIDE -> 12
        }
    }
    
    /**
     * Get tier color for display.
     */
    fun getTierColor(tier: RarityTier): Long {
        return when (tier) {
            RarityTier.COMMON -> 0xFF808080 // Gray
            RarityTier.UNCOMMON -> 0xFF4CAF50 // Green
            RarityTier.RARE -> 0xFF2196F3 // Blue
            RarityTier.LEGENDARY -> 0xFF9C27B0 // Purple
        }
    }
    
    /**
     * Get seed price by tier.
     */
    fun getSeedPrice(tier: RarityTier): Int {
        return when (tier) {
            RarityTier.COMMON -> 10
            RarityTier.UNCOMMON -> 50
            RarityTier.RARE -> 200
            RarityTier.LEGENDARY -> 1000
        }
    }
    
    /**
     * Calculate propagation success chance based on plant health.
     */
    fun getPropagationSuccessChance(plant: Plant): Float {
        return when {
            plant.health >= 90 -> 0.95f
            plant.health >= 80 -> 0.85f
            plant.health >= 70 -> 0.75f
            plant.health >= 60 -> 0.60f
            else -> 0.40f
        }
    }
}