package com.terrarium.app

import android.app.Application
import com.terrarium.app.util.NotificationHelper
import com.terrarium.app.work.PlantUpdateWorker
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class TerrariumApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Create notification channels
        NotificationHelper.createNotificationChannels(this)
        
        // Schedule background plant updates
        PlantUpdateWorker.schedule(this)
    }
}