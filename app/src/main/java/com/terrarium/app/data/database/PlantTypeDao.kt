package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.PlantType
import kotlinx.coroutines.flow.Flow

@Dao
interface PlantTypeDao {
    @Query("SELECT * FROM plant_types ORDER BY tier, name")
    fun getAllPlantTypes(): Flow<List<PlantType>>
    
    @Query("SELECT * FROM plant_types WHERE id = :id")
    suspend fun getPlantTypeById(id: Long): PlantType?
    
    @Query("SELECT * FROM plant_types WHERE tier = :tier")
    fun getPlantTypesByTier(tier: String): Flow<List<PlantType>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPlantTypes(plantTypes: List<PlantType>)
    
    @Query("SELECT COUNT(*) FROM plant_types")
    suspend fun getPlantTypeCount(): Int
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(plantTypes: List<PlantType>)
}