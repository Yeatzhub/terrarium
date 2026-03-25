package com.terrarium.app.util
import com.terrarium.app.R

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import android.provider.Settings
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Sound manager for playing game sound effects.
 * Uses SoundPool for low-latency playback.
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

class SoundManager(private val context: Context) {
    
    private val soundPool: SoundPool
    private var soundsLoaded = false
    
    // Sound IDs
    private var waterDropSound: Int = 0
    private var plantGrowSound: Int = 0
    private var coinSound: Int = 0
    private var levelUpSound: Int = 0
    
    // Sound enabled preference key
    private val soundEnabledKey = booleanPreferencesKey("sound_enabled")
    
    // Sound enabled state flow
    val soundEnabled: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[soundEnabledKey] ?: true // Default to enabled
    }
    
    init {
        val audioAttributes = AudioAttributes.Builder()
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .setUsage(AudioAttributes.USAGE_GAME)
            .build()
        
        soundPool = SoundPool.Builder()
            .setAudioAttributes(audioAttributes)
            .setMaxStreams(4)
            .build()
        
        soundPool.setOnLoadCompleteListener { _, sampleId, status ->
            if (status == 0) {
                soundsLoaded = true
            }
        }
        
        loadSounds()
    }
    
    private fun loadSounds() {
        try {
            waterDropSound = soundPool.load(context, R.raw.water_drop, 1)
            plantGrowSound = soundPool.load(context, R.raw.plant_grow, 1)
            coinSound = soundPool.load(context, R.raw.coin, 1)
            levelUpSound = soundPool.load(context, R.raw.level_up, 1)
        } catch (e: Exception) {
            // Sound files not found - this is optional feature
            // App will work silently without sounds
        }
    }
    
    /**
     * Play water drop sound when watering plants
     */
    suspend fun playWaterDrop() {
        if (isSoundEnabled() && soundsLoaded) {
            soundPool.play(waterDropSound, 0.7f, 0.7f, 1, 0, 1.0f)
        }
    }
    
    /**
     * Play plant grow sound when plant advances growth stage
     */
    suspend fun playPlantGrow() {
        if (isSoundEnabled() && soundsLoaded) {
            soundPool.play(plantGrowSound, 0.6f, 0.6f, 1, 0, 1.0f)
        }
    }
    
    /**
     * Play coin sound when making purchases or earning coins
     */
    suspend fun playCoin() {
        if (isSoundEnabled() && soundsLoaded) {
            soundPool.play(coinSound, 0.8f, 0.8f, 1, 0, 1.0f)
        }
    }
    
    /**
     * Play level up sound when player gains a level
     */
    suspend fun playLevelUp() {
        if (isSoundEnabled() && soundsLoaded) {
            soundPool.play(levelUpSound, 1.0f, 1.0f, 1, 0, 1.0f)
        }
    }
    
    /**
     * Release sound resources
     */
    fun release() {
        soundPool.release()
    }
    
    /**
     * Check if sound is enabled
     */
    private suspend fun isSoundEnabled(): Boolean {
        return soundEnabled.first()
    }
    
    /**
     * Toggle sound on/off
     */
    suspend fun setSoundEnabled(enabled: Boolean) {
        context.dataStore.updateData { preferences ->
            val mutablePreferences = preferences.toMutablePreferences()
            mutablePreferences[soundEnabledKey] = enabled
            mutablePreferences.toPreferences()
        }
    }
    
    companion object {
        @Volatile
        private var instance: SoundManager? = null
        
        fun getInstance(context: Context): SoundManager {
            return instance ?: synchronized(this) {
                instance ?: SoundManager(context.applicationContext).also { instance = it }
            }
        }
    }
}

/**
 * Extension to get first value from Flow
 */
private suspend fun <T> Flow<T>.first(): T {
    var result: T? = null
    collect { value ->
        result = value
        return@collect
    }
    return result!!
}