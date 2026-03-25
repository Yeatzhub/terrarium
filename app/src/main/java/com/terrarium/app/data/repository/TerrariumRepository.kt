package com.terrarium.app.data.repository

import com.terrarium.app.data.database.TerrariumDao
import com.terrarium.app.data.model.Terrarium
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TerrariumRepository @Inject constructor(
    private val terrariumDao: TerrariumDao
) {
    fun getAllTerrariums(): Flow<List<Terrarium>> = terrariumDao.getAllTerrariums()
    
    suspend fun getTerrariumById(id: Long): Terrarium? = terrariumDao.getTerrariumById(id)
    
    suspend fun createTerrarium(terrarium: Terrarium): Long = terrariumDao.insertTerrarium(terrarium)
    
    suspend fun updateTerrarium(terrarium: Terrarium) = terrariumDao.updateTerrarium(terrarium)
    
    suspend fun deleteTerrarium(terrarium: Terrarium) = terrariumDao.deleteTerrarium(terrarium)
    
    suspend fun getTerrariumCount(): Int = terrariumDao.getTerrariumCount()
}