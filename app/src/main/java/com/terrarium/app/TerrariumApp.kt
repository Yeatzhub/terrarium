package com.terrarium.app

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.terrarium.app.ui.home.HomeScreen
import com.terrarium.app.ui.shop.ShopScreen
import com.terrarium.app.ui.inventory.InventoryScreen
import com.terrarium.app.ui.social.SocialScreen

sealed class Screen(val route: String, val title: String, val icon: String) {
    object Home : Screen("home", "Terrarium", "🌿")
    object Shop : Screen("shop", "Shop", "🛒")
    object Inventory : Screen("inventory", "Inventory", "📦")
    object Social : Screen("social", "Social", "👥")
}

@Composable
fun TerrariumApp(
    navController: NavHostController = rememberNavController()
) {
    Surface(
        modifier = androidx.compose.ui.Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        NavHost(
            navController = navController,
            startDestination = Screen.Home.route
        ) {
            composable(Screen.Home.route) {
                HomeScreen(
                    onNavigateToShop = { navController.navigate(Screen.Shop.route) },
                    onNavigateToInventory = { navController.navigate(Screen.Inventory.route) }
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
        }
    }
}