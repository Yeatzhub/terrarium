package com.terrarium.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.lifecycleScope
import com.terrarium.app.data.model.BaseLayerConfig
import com.terrarium.app.data.preferences.UserPreferences
import com.terrarium.app.data.repository.GameInitializer
import com.terrarium.app.ui.theme.TerrariumTheme
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    @Inject
    lateinit var userPreferences: UserPreferences
    
    @Inject
    lateinit var gameInitializer: GameInitializer
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            TerrariumTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val hasCompletedOnboarding by userPreferences.hasCompletedOnboarding
                        .collectAsState(initial = false)
                    
                    TerrariumApp(
                        hasCompletedOnboarding = hasCompletedOnboarding,
                        onOnboardingComplete = {
                            lifecycleScope.launch {
                                userPreferences.setOnboardingComplete(true)
                            }
                        },
                        onBaseLayerComplete = { config ->
                            lifecycleScope.launch {
                                // Update the first terrarium with base layers
                                gameInitializer.updateBaseLayers(config)
                            }
                        }
                    )
                }
            }
        }
    }
}