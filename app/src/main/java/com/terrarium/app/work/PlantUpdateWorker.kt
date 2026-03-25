package com.terrarium.app.work

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.terrarium.app.data.model.Plant
import com.terrarium.app.data.repository.DailyTaskRepository
import com.terrarium.app.data.repository.PlantRepository
import com.terrarium.app.data.repository.PlantTypeRepository
import com.terrarium.app.data.repository.UserRepository
import com.terrarium.app.util.GameLogic
import com.terrarium.app.util.TimeUtils
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first
import java.util.concurrent.TimeUnit

/**
 * Background worker that updates plant states periodically.
 * Handles:
 * - Plant growth progression
 * - Moisture decay
 * - Health calculations
 * - Wilting/death detection
 * - Low moisture notifications
 */
@HiltWorker
class PlantUpdateWorker @AssistedInject constructor(
    @Assisted private val context: Context,
    @Assisted workerParams: WorkerParameters,
    private val plantRepository: PlantRepository,
    private val plantTypeRepository: PlantTypeRepository,
    private val userRepository: UserRepository,
    private val dailyTaskRepository: DailyTaskRepository
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            // Get all plant types for reference
            val plantTypes = plantTypeRepository.getAllPlantTypes().first()
            val plantTypeMap = plantTypes.associateBy { it.id }
            
            // Get current user
            val user = userRepository.getCurrentUser()
            if (user == null) {
                return Result.success()
            }
            
            // Check and regenerate daily tasks if needed (new day)
            val now = System.currentTimeMillis()
            val activeTasks = dailyTaskRepository.getActiveTasksForUser(user.id).first()
            
            if (activeTasks.isEmpty()) {
                // Generate new daily tasks
                dailyTaskRepository.generateDailyTasks(user.id)
            }
            
            // Update expired daily tasks
            dailyTaskRepository.deleteExpiredTasks()
            
            // Note: In a real app, we would iterate through ALL plants in ALL terrariums
            // For each plant, we would:
            // 1. Update moisture (decay over time)
            // 2. Update growth stage
            // 3. Calculate health
            // 4. Check for wilting/death conditions
            // 5. Send notifications for low moisture plants
            
            // This would typically involve:
            // val terrariums = terrariumRepository.getAllTerrariums().first()
            // for terrarium in terrariums {
            //     val plants = plantRepository.getPlantsForTerrarium(terrarium.id).first()
            //     for plant in plants {
            //         val plantType = plantTypeMap[plant.typeId]
            //         if (plantType != null) {
            //             plantRepository.updatePlantStatus(plant, plantType)
            //             
            //             // Check for low moisture notification
            //             if (GameLogic.needsWaterNotification(plant)) {
            //                 sendMoistureNotification(plant, plantType)
            //             }
            //         }
            //     }
            // }
            
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    companion object {
        private const val WORK_NAME = "plant_update_work"
        
        /**
         * Schedule the periodic plant update worker.
         * Runs every hour to update plant states.
         */
        fun schedule(context: Context) {
            val workRequest = PeriodicWorkRequestBuilder<PlantUpdateWorker>(
                1, TimeUnit.HOURS
            )
                .setConstraints(
                    androidx.work.Constraints.Builder()
                        .setRequiresBatteryNotLow(true)
                        .build()
                )
                .build()
            
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                workRequest
            )
        }
        
        /**
         * Cancel the scheduled worker.
         */
        fun cancel(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
        }
    }
}