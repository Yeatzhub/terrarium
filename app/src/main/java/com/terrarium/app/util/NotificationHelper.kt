package com.terrarium.app.util

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.terrarium.app.MainActivity
import com.terrarium.app.R
import com.terrarium.app.data.model.Plant
import com.terrarium.app.data.model.PlantType

/**
 * Helper class for creating and managing notifications.
 */
object NotificationHelper {
    
    const val CHANNEL_ID_PLANT_CARE = "plant_care"
    const val CHANNEL_ID_DAILY_TASKS = "daily_tasks"
    const val CHANNEL_ID_PROGRESS = "progress"
    
    const val NOTIFICATION_ID_LOW_MOISTURE = 1001
    const val NOTIFICATION_ID_DAILY_LOGIN = 1002
    const val NOTIFICATION_ID_DAILY_TASKS = 1003
    const val NOTIFICATION_ID_LEVEL_UP = 1004
    const val NOTIFICATION_ID_PROPAGATION_READY = 1005
    
    /**
     * Create notification channels for Android O+.
     */
    fun createNotificationChannels(context: Context) {
        val channelPlantCare = NotificationChannel(
            CHANNEL_ID_PLANT_CARE,
            "Plant Care",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Notifications about your plants' health and care needs"
        }
        
        val channelDailyTasks = NotificationChannel(
            CHANNEL_ID_DAILY_TASKS,
            "Daily Tasks",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Daily task reminders and completions"
        }
        
        val channelProgress = NotificationChannel(
            CHANNEL_ID_PROGRESS,
            "Progress",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Level ups and achievements"
        }
        
        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.createNotificationChannels(
            listOf(channelPlantCare, channelDailyTasks, channelProgress)
        )
    }
    
    /**
     * Show a low moisture notification for a plant.
     */
    fun showMoistureNotification(
        context: Context,
        plant: Plant,
        plantType: PlantType
    ) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            plant.id.toInt(),
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(context, CHANNEL_ID_PLANT_CARE)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("${plantType.emoji} ${plantType.name} needs water!")
            .setContentText("Moisture is at ${(plant.moisture * 100).toInt()}%. Water your plant to keep it healthy!")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(context).notify(
            NOTIFICATION_ID_LOW_MOISTURE + plant.id.toInt(),
            notification
        )
    }
    
    /**
     * Show a daily login bonus notification.
     */
    fun showDailyLoginNotification(
        context: Context,
        coinsGained: Int,
        xpGained: Int,
        streak: Int
    ) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val title = if (streak > 1) {
            "🔥 $streak day streak! Daily bonus collected!"
        } else {
            "👋 Welcome back! Daily bonus collected!"
        }
        
        val notification = NotificationCompat.Builder(context, CHANNEL_ID_DAILY_TASKS)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText("+$coinsGained coins, +$xpGained XP")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(context).notify(
            NOTIFICATION_ID_DAILY_LOGIN,
            notification
        )
    }
    
    /**
     * Show a level up notification.
     */
    fun showLevelUpNotification(
        context: Context,
        newLevel: Int,
        unlockedJars: List<String>
    ) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val contentText = if (unlockedJars.isNotEmpty()) {
            "You unlocked: ${unlockedJars.joinToString(", ")}"
        } else {
            "Keep growing those plants!"
        }
        
        val notification = NotificationCompat.Builder(context, CHANNEL_ID_PROGRESS)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("🎉 Level $newLevel Reached!")
            .setContentText(contentText)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(context).notify(
            NOTIFICATION_ID_LEVEL_UP,
            notification
        )
    }
    
    /**
     * Show a propagation ready notification.
     */
    fun showPropagationReadyNotification(
        context: Context,
        plantTypeName: String,
        emoji: String
    ) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(context, CHANNEL_ID_PLANT_CARE)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("✂️ Cutting Ready!")
            .setContentText("Your $emoji $plantTypeName cutting is ready to plant!")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(context).notify(
            NOTIFICATION_ID_PROPAGATION_READY,
            notification
        )
    }
    
    /**
     * Show a daily task completion reminder.
     */
    fun showDailyTaskReminder(
        context: Context,
        tasksRemaining: Int
    ) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(context, CHANNEL_ID_DAILY_TASKS)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("📋 Daily Tasks")
            .setContentText("You have $tasksRemaining tasks remaining today!")
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        NotificationManagerCompat.from(context).notify(
            NOTIFICATION_ID_DAILY_TASKS,
            notification
        )
    }
}