package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.GrowthStage
import com.terrarium.app.data.model.Plant
import kotlinx.coroutines.flow.Flow

@Dao
interface PlantDao {
    @Query("SELECT * FROM plants WHERE terrariumId = :terrariumId ORDER BY plantedAt DESC")
    fun getPlantsForTerrarium(terrariumId: Long): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE id = :id")
    suspend fun getPlantById(id: Long): Plant?
    
    @Query("SELECT * FROM plants ORDER BY plantedAt DESC")
    fun getAllPlants(): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE growthStage = :stage")
    fun getPlantsByStage(stage: GrowthStage): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE terrariumId = :terrariumId AND growthStage = :stage")
    fun getPlantsForTerrariumByStage(terrariumId: Long, stage: GrowthStage): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE isDead = 0")
    fun getLivingPlants(): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE terrariumId = :terrariumId AND isDead = 0")
    fun getLivingPlantsForTerrarium(terrariumId: Long): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE moisture < :threshold AND isDead = 0")
    fun getPlantsNeedingWater(threshold: Float = 0.3f): Flow<List<Plant>>
    
    @Query("SELECT * FROM plants WHERE growthStage = 'MATURE' AND health >= 70 AND isDead = 0")
    fun getPlantsReadyToPropagate(): Flow<List<Plant>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPlant(plant: Plant): Long
    
    @Update
    suspend fun updatePlant(plant: Plant)
    
    @Delete
    suspend fun deletePlant(plant: Plant)
    
    @Query("DELETE FROM plants WHERE terrariumId = :terrariumId")
    suspend fun deletePlantsForTerrarium(terrariumId: Long)
    
    @Query("DELETE FROM plants WHERE isDead = 1")
    suspend fun deleteDeadPlants()
    
    @Query("DELETE FROM plants WHERE isDead = 1 AND terrariumId = :terrariumId")
    suspend fun deleteDeadPlantsForTerrarium(terrariumId: Long)
    
    @Query("UPDATE plants SET moisture = moisture - :decayAmount WHERE id = :plantId")
    suspend fun decayMoisture(plantId: Long, decayAmount: Float)
    
    @Query("UPDATE plants SET daysNeglected = daysNeglected + 1 WHERE moisture < :threshold AND isDead = 0")
    suspend fun incrementNeglectForDryPlants(threshold: Float = 0.15f)
    
    @Query("UPDATE plants SET lastChecked = :timestamp WHERE id = :plantId")
    suspend fun updateLastChecked(plantId: Long, timestamp: Long = System.currentTimeMillis())
    
    @Query("SELECT COUNT(*) FROM plants WHERE terrariumId = :terrariumId AND isDead = 0")
    suspend fun getLivingPlantCountForTerrarium(terrariumId: Long): Int
}