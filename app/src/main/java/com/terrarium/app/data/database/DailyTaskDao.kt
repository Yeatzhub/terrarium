package com.terrarium.app.data.database

import androidx.room.*
import com.terrarium.app.data.model.DailyTask
import kotlinx.coroutines.flow.Flow

@Dao
interface DailyTaskDao {
    @Query("SELECT * FROM daily_tasks WHERE userId = :userId AND expiresAt > :currentTime ORDER BY createdAt DESC")
    fun getActiveTasksForUser(userId: Long, currentTime: Long = System.currentTimeMillis()): Flow<List<DailyTask>>
    
    @Query("SELECT * FROM daily_tasks WHERE id = :id")
    suspend fun getTaskById(id: Long): DailyTask?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: DailyTask): Long
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTasks(tasks: List<DailyTask>)
    
    @Update
    suspend fun updateTask(task: DailyTask)
    
    @Delete
    suspend fun deleteTask(task: DailyTask)
    
    @Query("DELETE FROM daily_tasks WHERE userId = :userId")
    suspend fun deleteAllTasksForUser(userId: Long)
    
    @Query("DELETE FROM daily_tasks WHERE expiresAt < :currentTime")
    suspend fun deleteExpiredTasks(currentTime: Long = System.currentTimeMillis())
    
    @Query("UPDATE daily_tasks SET currentCount = currentCount + 1, isCompleted = 1 WHERE id = :taskId AND currentCount + 1 >= targetCount")
    suspend fun completeTask(taskId: Long)
    
    @Query("UPDATE daily_tasks SET currentCount = currentCount + 1 WHERE id = :taskId")
    suspend fun incrementTaskProgress(taskId: Long)
    
    @Query("SELECT COUNT(*) FROM daily_tasks WHERE userId = :userId AND isCompleted = 1 AND expiresAt > :currentTime")
    suspend fun getCompletedTasksCount(userId: Long, currentTime: Long = System.currentTimeMillis()): Int
}