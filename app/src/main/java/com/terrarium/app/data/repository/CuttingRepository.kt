package com.terrarium.app.data.repository

import com.terrarium.app.data.database.CuttingDao
import com.terrarium.app.data.model.Cutting
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CuttingRepository @Inject constructor(
    private val cuttingDao: CuttingDao
) {
    fun getCuttingsForUser(userId: Long): Flow<List<Cutting>> = 
        cuttingDao.getCuttingsForUser(userId)
    
    fun getReadyCuttings(userId: Long): Flow<List<Cutting>> = 
        cuttingDao.getReadyCuttings(userId)
    
    suspend fun getCuttingById(id: Long): Cutting? = cuttingDao.getCuttingById(id)
    
    suspend fun createCutting(cutting: Cutting): Long = cuttingDao.insertCutting(cutting)
    
    suspend fun updateCutting(cutting: Cutting) = cuttingDao.updateCutting(cutting)
    
    suspend fun deleteCutting(cutting: Cutting) = cuttingDao.deleteCutting(cutting)
    
    suspend fun deleteCuttingById(id: Long) = cuttingDao.deleteCuttingById(id)
    
    suspend fun updateReadyCuttings() = cuttingDao.updateReadyCuttings()
}