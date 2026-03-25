package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.Cutting
import kotlinx.coroutines.flow.Flow

@Dao
interface CuttingDao {
    @Query("SELECT * FROM cuttings WHERE userId = :userId ORDER BY createdAt DESC")
    fun getCuttingsForUser(userId: Long): Flow<List<Cutting>>
    
    @Query("SELECT * FROM cuttings WHERE userId = :userId AND isReady = 1")
    fun getReadyCuttings(userId: Long): Flow<List<Cutting>>
    
    @Query("SELECT * FROM cuttings WHERE id = :id")
    suspend fun getCuttingById(id: Long): Cutting?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCutting(cutting: Cutting): Long
    
    @Update
    suspend fun updateCutting(cutting: Cutting)
    
    @Delete
    suspend fun deleteCutting(cutting: Cutting)
    
    @Query("DELETE FROM cuttings WHERE id = :id")
    suspend fun deleteCuttingById(id: Long)
    
    @Query("UPDATE cuttings SET isReady = 1 WHERE readyAt <= :currentTime AND isReady = 0")
    suspend fun updateReadyCuttings(currentTime: Long = System.currentTimeMillis())
}