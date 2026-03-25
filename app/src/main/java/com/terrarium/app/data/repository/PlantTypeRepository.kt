package com.terrarium.app.data.repository

import com.terrarium.app.data.database.PlantTypeDao
import com.terrarium.app.data.model.PlantType
import com.terrarium.app.data.model.RarityTier
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PlantTypeRepository @Inject constructor(
    private val plantTypeDao: PlantTypeDao
) {
    fun getAllPlantTypes(): Flow<List<PlantType>> = plantTypeDao.getAllPlantTypes()
    
    suspend fun getPlantTypeById(id: Long): PlantType? = plantTypeDao.getPlantTypeById(id)
    
    fun getPlantTypesByTier(tier: RarityTier): Flow<List<PlantType>> = 
        plantTypeDao.getPlantTypesByTier(tier.name)
}