package com.terrarium.app.data.repository

import com.terrarium.app.data.database.DailyTaskDao
import com.terrarium.app.data.model.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DailyTaskRepository @Inject constructor(
    private val dailyTaskDao: DailyTaskDao
) {
    fun getActiveTasksForUser(userId: Long): Flow<List<DailyTask>> = 
        dailyTaskDao.getActiveTasksForUser(userId)
    
    suspend fun getTaskById(id: Long): DailyTask? = dailyTaskDao.getTaskById(id)
    
    suspend fun insertTask(task: DailyTask): Long = dailyTaskDao.insertTask(task)
    
    suspend fun insertTasks(tasks: List<DailyTask>) = dailyTaskDao.insertTasks(tasks)
    
    suspend fun updateTask(task: DailyTask) = dailyTaskDao.updateTask(task)
    
    suspend fun deleteTask(task: DailyTask) = dailyTaskDao.deleteTask(task)
    
    suspend fun deleteAllTasksForUser(userId: Long) = dailyTaskDao.deleteAllTasksForUser(userId)
    
    suspend fun deleteExpiredTasks() = dailyTaskDao.deleteExpiredTasks()
    
    suspend fun incrementTaskProgress(taskId: Long) = dailyTaskDao.incrementTaskProgress(taskId)
    
    suspend fun completeTask(taskId: Long) = dailyTaskDao.completeTask(taskId)
    
    suspend fun getCompletedTasksCount(userId: Long): Int = dailyTaskDao.getCompletedTasksCount(userId)
    
    /**
     * Generate random daily tasks for a user.
     */
    suspend fun generateDailyTasks(userId: Long) {
        // Delete old tasks
        dailyTaskDao.deleteAllTasksForUser(userId)
        
        // Get random task templates
        val templates = DailyTaskTemplates.getRandomTasks(4)
        val now = System.currentTimeMillis()
        val tomorrow = now + (24 * 60 * 60 * 1000)
        
        val tasks = templates.map { template ->
            DailyTask(
                userId = userId,
                name = template.name,
                description = template.description,
                xpReward = template.xpReward,
                coinsReward = template.coinsReward,
                taskType = template.taskType,
                targetCount = template.targetCount,
                createdAt = now,
                expiresAt = tomorrow
            )
        }
        
        dailyTaskDao.insertTasks(tasks)
    }
    
    /**
     * Update progress on a task type.
     */
    suspend fun updateTaskProgress(userId: Long, taskType: TaskType) {
        // Get active tasks of this type
        dailyTaskDao.getActiveTasksForUser(userId).collect { tasks ->
            tasks.filter { it.taskType == taskType && !it.isCompleted }.forEach { task ->
                if (task.currentCount + 1 >= task.targetCount) {
                    dailyTaskDao.completeTask(task.id)
                } else {
                    dailyTaskDao.incrementTaskProgress(task.id)
                }
            }
        }
    }
}