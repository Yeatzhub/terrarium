package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.User

@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id")
    suspend fun getUserById(id: Long): User?
    
    @Query("SELECT * FROM users LIMIT 1")
    suspend fun getCurrentUser(): User?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: User): Long
    
    @Update
    suspend fun updateUser(user: User)
    
    @Query("UPDATE users SET xp = xp + :xpGain WHERE id = :userId")
    suspend fun addXp(userId: Long, xpGain: Long)
    
    @Query("UPDATE users SET coins = coins + :amount WHERE id = :userId")
    suspend fun addCoins(userId: Long, amount: Int)
}