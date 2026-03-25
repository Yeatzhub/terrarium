package com.terrarium.app

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.terrarium.app.ui.home.HomeScreen
import com.terrarium.app.ui.shop.ShopScreen
import com.terrarium.app.ui.inventory.InventoryScreen
import com.terrarium.app.ui.social.SocialScreen
import com.terrarium.app.ui.onboarding.OnboardingScreen
import com.terrarium.app.ui.settings.SettingsScreen
import kotlinx.coroutines.flow.first

sealed class Screen(val route: String, val title: String, val icon: String) {
    object Home : Screen("home", "Terrarium", "🌿")
    object Shop : Screen("shop", "Shop", "🛒")
    object Inventory : Screen("inventory", "Inventory", "📦")
    object Social : Screen("social", "Social", "👥")
    object Onboarding : Screen("onboarding", "Welcome", "🌟")
    object Settings : Screen("settings", "Settings", "⚙️")
}

@Composable
fun TerrariumApp(
    navController: NavHostController = rememberNavController(),
    hasCompletedOnboarding: Boolean = false
) {
    // Determine start destination based on onboarding status
    val startDestination = if (hasCompletedOnboarding) Screen.Home.route else Screen.Onboarding.route
    
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        NavHost(
            navController = navController,
            startDestination = startDestination
        ) {
            // Onboarding flow
            composable(Screen.Onboarding.route) {
                OnboardingScreen(
                    onComplete = {
                        // Navigate to home and clear back stack
                        navController.navigate(Screen.Home.route) {
                            popUpTo(Screen.Onboarding.route) { inclusive = true }
                        }
                    }
                )
            }
            
            composable(Screen.Home.route) {
                HomeScreen(
                    onNavigateToShop = { navController.navigate(Screen.Shop.route) },
                    onNavigateToInventory = { navController.navigate(Screen.Inventory.route) },
                    onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
                )
            }
            composable(Screen.Shop.route) {
                ShopScreen(
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Screen.Inventory.route) {
                InventoryScreen(
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Screen.Social.route) {
                SocialScreen(
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Screen.Settings.route) {
                SettingsScreen(
                    onBack = { navController.popBackStack() },
                    onResetGame = {
                        // Reset game and return to onboarding
                        navController.navigate(Screen.Onboarding.route) {
                            popUpTo(Screen.Home.route) { inclusive = true }
                        }
                    }
                )
            }
        }
    }
}