package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.Terrarium
import kotlinx.coroutines.flow.Flow

@Dao
interface TerrariumDao {
    @Query("SELECT * FROM terrariums ORDER BY createdAt DESC")
    fun getAllTerrariums(): Flow<List<Terrarium>>
    
    @Query("SELECT * FROM terrariums WHERE id = :id")
    suspend fun getTerrariumById(id: Long): Terrarium?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTerrarium(terrarium: Terrarium): Long
    
    @Update
    suspend fun updateTerrarium(terrarium: Terrarium)
    
    @Delete
    suspend fun deleteTerrarium(terrarium: Terrarium)
    
    @Query("SELECT COUNT(*) FROM terrariums")
    suspend fun getTerrariumCount(): Int
}