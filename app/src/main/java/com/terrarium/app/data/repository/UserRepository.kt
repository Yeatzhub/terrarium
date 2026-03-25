package com.terrarium.app.data.repository

import com.terrarium.app.data.database.UserDao
import com.terrarium.app.data.model.JarType
import com.terrarium.app.data.model.LevelRewards
import com.terrarium.app.data.model.User
import com.terrarium.app.util.GameLogic
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UserRepository @Inject constructor(
    private val userDao: UserDao
) {
    suspend fun getCurrentUser(): User? = userDao.getCurrentUser()
    
    suspend fun getUserById(id: Long): User? = userDao.getUserById(id)
    
    suspend fun createUser(name: String = "Gardener"): Long {
        return userDao.insertUser(User(name = name))
    }
    
    suspend fun updateUser(user: User) = userDao.updateUser(user)
    
    suspend fun addXp(userId: Long, xpGain: Long): LevelUpResult {
        val user = userDao.getUserById(userId) ?: return LevelUpResult(xpGain, false, emptyList())
        
        val newXp = user.xp + xpGain
        val currentLevel = user.level
        val newLevel = GameLogic.levelFromXp(newXp)
        
        // Check for level up
        val didLevelUp = newLevel > currentLevel
        val unlockedJars = mutableListOf<JarType>()
        
        if (didLevelUp) {
            // Check for new jar unlocks
            for (level in (currentLevel + 1)..newLevel) {
                val reward = LevelRewards.getRewardForLevel(level)
                if (reward != null) {
                    unlockedJars.addAll(reward.jarUnlocks)
                }
            }
        }
        
        // Update user
        val updatedUser = user.copy(
            xp = newXp,
            level = newLevel,
            unlockedJarTypes = if (unlockedJars.isNotEmpty()) {
                val existing = user.getUnlockedJarTypes().toMutableList()
                existing.addAll(unlockedJars)
                existing.joinToString(",") { it.name }
            } else {
                user.unlockedJarTypes
            }
        )
        
        userDao.updateUser(updatedUser)
        return LevelUpResult(xpGain, didLevelUp, unlockedJars)
    }
    
    suspend fun addCoins(userId: Long, amount: Int) {
        userDao.addCoins(userId, amount)
    }
    
    suspend fun deductCoins(userId: Long, amount: Int): Boolean {
        val user = userDao.getUserById(userId) ?: return false
        if (user.coins < amount) return false
        
        userDao.updateUser(user.copy(coins = user.coins - amount))
        return true
    }
    
    suspend fun recordDailyLogin(userId: Long): DailyLoginResult {
        val user = userDao.getUserById(userId) ?: return DailyLoginResult(0, 0, false)
        
        val now = System.currentTimeMillis()
        val lastLogin = user.lastLogin
        val dayInMillis = 24 * 60 * 60 * 1000L
        
        // Check if this is a new day
        val isNewDay = (now - lastLogin) >= dayInMillis
        
        if (!isNewDay) {
            return DailyLoginResult(0, 0, false) // Already logged in today
        }
        
        // Calculate streak
        val twoDaysInMillis = 2 * dayInMillis
        val streakMaintained = (now - lastLogin) < twoDaysInMillis
        val newStreak = if (streakMaintained) user.dailyStreak + 1 else 1
        
        // Calculate rewards
        val coins = GameLogic.calculateDailyLoginCoins(newStreak)
        val xp = GameLogic.calculateDailyLoginXp(newStreak)
        
        // Update user
        val updatedUser = user.copy(
            dailyStreak = newStreak,
            lastLogin = now
        )
        
        userDao.updateUser(updatedUser)
        userDao.addCoins(userId, coins)
        userDao.addXp(userId, xp.toLong())
        
        return DailyLoginResult(coins, xp, true)
    }
    
    suspend fun getUnlockedJarTypes(userId: Long): List<JarType> {
        val user = userDao.getUserById(userId) ?: return listOf(JarType.SMALL)
        return user.getUnlockedJarTypes()
    }
    
    suspend fun hasSufficientCoins(userId: Long, amount: Int): Boolean {
        val user = userDao.getUserById(userId) ?: return false
        return user.coins >= amount
    }
    
    fun getUserFlow(userId: Long): Flow<User?> = 
        kotlinx.coroutines.flow.flow { emit(userDao.getUserById(userId)) }
}

/**
 * Result of adding XP with level up info.
 */
data class LevelUpResult(
    val xpGained: Long,
    val didLevelUp: Boolean,
    val unlockedJars: List<JarType>
)

/**
 * Result of daily login.
 */
data class DailyLoginResult(
    val coinsGained: Int,
    val xpGained: Int,
    val wasNewLogin: Boolean
)