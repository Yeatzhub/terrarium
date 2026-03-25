package com.terrarium.app.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * User preferences stored locally on device.
 * Handles onboarding, settings, and other user-specific data.
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

class UserPreferences(private val context: Context) {
    
    // Preference Keys
    private val hasCompletedOnboardingKey = booleanPreferencesKey("has_completed_onboarding")
    private val soundEnabledKey = booleanPreferencesKey("sound_enabled")
    private val notificationsEnabledKey = booleanPreferencesKey("notifications_enabled")
    
    /**
     * Check if user has completed onboarding
     */
    val hasCompletedOnboarding: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[hasCompletedOnboardingKey] ?: false
    }
    
    /**
     * Sound enabled preference
     */
    val soundEnabled: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[soundEnabledKey] ?: true
    }
    
    /**
     * Notifications enabled preference
     */
    val notificationsEnabled: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[notificationsEnabledKey] ?: true
    }
    
    /**
     * Mark onboarding as complete
     */
    suspend fun setOnboardingComplete(complete: Boolean = true) {
        context.dataStore.edit { preferences ->
            preferences[hasCompletedOnboardingKey] = complete
        }
    }
    
    /**
     * Toggle sound
     */
    suspend fun setSoundEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[soundEnabledKey] = enabled
        }
    }
    
    /**
     * Toggle notifications
     */
    suspend fun setNotificationsEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[notificationsEnabledKey] = enabled
        }
    }
    
    /**
     * Clear all preferences (for game reset)
     */
    suspend fun clearAll() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
    
    companion object {
        @Volatile
        private var instance: UserPreferences? = null
        
        fun getInstance(context: Context): UserPreferences {
            return instance ?: synchronized(this) {
                instance ?: UserPreferences(context.applicationContext).also { instance = it }
            }
        }
    }
}