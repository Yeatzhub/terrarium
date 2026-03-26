package com.terrarium.app.ui.shop

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.terrarium.app.data.model.*
import com.terrarium.app.viewmodel.HomeViewModel
import com.terrarium.app.viewmodel.ShopViewModel
import com.terrarium.app.util.GameLogic
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShopScreen(
    viewModel: ShopViewModel = hiltViewModel(),
    onBack: () -> Unit = {}
) {
    var selectedTab by remember { mutableStateOf(0) }
    val tabs = listOf("Seeds", "Jars", "Decorations")
    val user by viewModel.user.collectAsState()
    val message by viewModel.message.collectAsState()
    
    // Show message snackbar
    LaunchedEffect(message) {
        // Message will auto-clear after being shown
        viewModel.clearMessage()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("🛒 Shop")
                        Spacer(modifier = Modifier.width(16.dp))
                        // Show coins
                        Surface(
                            color = MaterialTheme.colorScheme.secondaryContainer,
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(text = "🪙", fontSize = 16.sp)
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "${user?.coins ?: 0}",
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Tab row
            TabRow(selectedTabIndex = selectedTab) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        text = { Text(title) }
                    )
                }
            }
            
            // Content based on tab
            when (selectedTab) {
                0 -> SeedShop(viewModel = viewModel)
                1 -> JarShop(viewModel = viewModel)
                2 -> DecorationShop(viewModel = viewModel)
            }
        }
    }
    
    // Show message if any
    message?.let { msg ->
        Snackbar(
            modifier = Modifier.padding(16.dp),
            action = {
                TextButton(onClick = { viewModel.clearMessage() }) {
                    Text("Dismiss")
                }
            }
        ) {
            Text(msg)
        }
    }
}

@Composable
private fun SeedShop(viewModel: ShopViewModel) {
    val commonPlants by viewModel.commonPlants.collectAsState()
    val uncommonPlants by viewModel.uncommonPlants.collectAsState()
    val rarePlants by viewModel.rarePlants.collectAsState()
    val legendaryPlants by viewModel.legendaryPlants.collectAsState()
    val user by viewModel.user.collectAsState()
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Common seeds
        if (commonPlants.isNotEmpty()) {
            item {
                SectionHeader("🌱 Common Seeds", "10 🪙 each • Level 1+")
            }
            items(commonPlants) { plant ->
                SeedCard(
                    plant = plant,
                    price = GameLogic.getSeedPrice(plant.tier),
                    canAfford = (user?.coins ?: 0) >= GameLogic.getSeedPrice(plant.tier),
                    hasLevel = (user?.level ?: 1) >= 1,
                    onBuy = { viewModel.purchaseSeed(plant) }
                )
            }
        }
        
        // Uncommon seeds
        if (uncommonPlants.isNotEmpty()) {
            item {
                SectionHeader("🌿 Uncommon Seeds", "50 🪙 each • Level 3+")
            }
            items(uncommonPlants) { plant ->
                SeedCard(
                    plant = plant,
                    price = GameLogic.getSeedPrice(plant.tier),
                    canAfford = (user?.coins ?: 0) >= GameLogic.getSeedPrice(plant.tier),
                    hasLevel = (user?.level ?: 1) >= 3,
                    onBuy = { viewModel.purchaseSeed(plant) }
                )
            }
        }
        
        // Rare seeds
        if (rarePlants.isNotEmpty()) {
            item {
                SectionHeader("✨ Rare Seeds", "200 🪙 each • Level 7+")
            }
            items(rarePlants) { plant ->
                SeedCard(
                    plant = plant,
                    price = GameLogic.getSeedPrice(plant.tier),
                    canAfford = (user?.coins ?: 0) >= GameLogic.getSeedPrice(plant.tier),
                    hasLevel = (user?.level ?: 1) >= 7,
                    onBuy = { viewModel.purchaseSeed(plant) }
                )
            }
        }
        
        // Legendary seeds
        if (legendaryPlants.isNotEmpty()) {
            item {
                SectionHeader("🌙 Legendary Seeds", "1000 🪙 each • Level 12+")
            }
            items(legendaryPlants) { plant ->
                SeedCard(
                    plant = plant,
                    price = GameLogic.getSeedPrice(plant.tier),
                    canAfford = (user?.coins ?: 0) >= GameLogic.getSeedPrice(plant.tier),
                    hasLevel = (user?.level ?: 1) >= 12,
                    onBuy = { viewModel.purchaseSeed(plant) }
                )
            }
        }
    }
}

@Composable
private fun JarShop(viewModel: ShopViewModel) {
    val user by viewModel.user.collectAsState()
    val jars = listOf(
        JarShopItem(JarType.SMALL, "Small Jar", "Perfect for beginners. 3 plant capacity.", 0, 1),
        JarShopItem(JarType.MEDIUM, "Medium Jar", "Standard-sized terrarium. 5 plant capacity.", 100, 3),
        JarShopItem(JarType.ROUND, "Round Jar", "360° viewing angle. 4 plant capacity.", 150, 7),
        JarShopItem(JarType.TALL, "Tall Jar", "For taller plants. 6 plant capacity.", 200, 7),
        JarShopItem(JarType.WIDE, "Wide Jar", "Extra horizontal space. 7 plant capacity.", 250, 12)
    )
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(jars) { jar ->
            val isUnlocked = user?.hasJarUnlocked(jar.type) ?: false
            val canAfford = (user?.coins ?: 0) >= jar.price
            val hasLevel = (user?.level ?: 1) >= jar.requiredLevel
            
            JarCard(
                jar = jar,
                isUnlocked = isUnlocked,
                canAfford = canAfford,
                hasLevel = hasLevel,
                onBuy = {
                    viewModel.purchaseJar(
                        ShopItem(
                            id = when (jar.type) {
                                JarType.SMALL -> 101L
                                JarType.MEDIUM -> 102L
                                JarType.ROUND -> 103L
                                JarType.TALL -> 104L
                                JarType.WIDE -> 105L
                            },
                            name = jar.name,
                            description = jar.description,
                            itemType = com.terrarium.app.data.model.ItemType.JAR_UNLOCK,
                            price = jar.price,
                            emoji = "🏺",
                            requiredLevel = jar.requiredLevel
                        )
                    )
                }
            )
        }
    }
}

@Composable
private fun DecorationShop(viewModel: ShopViewModel) {
    val user by viewModel.user.collectAsState()
    val decorations = listOf(
        ShopItem(201, "Pebbles", "Decorative stones for your terrarium", 
            com.terrarium.app.data.model.ItemType.DECORATION, 25, "🪨", 1),
        ShopItem(202, "Miniature Bench", "Tiny garden bench for your plants", 
            com.terrarium.app.data.model.ItemType.DECORATION, 50, "🪑", 3),
        ShopItem(203, "Fairy House", "Cozy fairy dwelling for a magical touch", 
            com.terrarium.app.data.model.ItemType.DECORATION, 100, "🏠", 5),
        ShopItem(204, "Crystal Cluster", "Sparkly crystals for decoration", 
            com.terrarium.app.data.model.ItemType.DECORATION, 75, "💎", 5),
        ShopItem(205, "Mini Lake", "Tiny pond for visual appeal", 
            com.terrarium.app.data.model.ItemType.DECORATION, 150, "🌊", 7)
    )
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(decorations) { item ->
            val canAfford = (user?.coins ?: 0) >= item.price
            val hasLevel = (user?.level ?: 1) >= item.requiredLevel
            
            DecorationCard(
                item = item,
                canAfford = canAfford,
                hasLevel = hasLevel,
                onBuy = { viewModel.purchaseDecoration(item) }
            )
        }
    }
}

@Composable
private fun SectionHeader(title: String, subtitle: String = "") {
    Column(modifier = Modifier.padding(vertical = 8.dp)) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        if (subtitle.isNotEmpty()) {
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun SeedCard(
    plant: PlantType,
    price: Int,
    canAfford: Boolean,
    hasLevel: Boolean,
    onBuy: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = plant.emoji, fontSize = 32.sp)
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = plant.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = plant.scientificName,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "${plant.growthTimeHours}h to grow",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                )
            }
            
            Button(
                onClick = onBuy,
                enabled = canAfford && hasLevel
            ) {
                Text("$price 🪙")
            }
        }
    }
}

data class JarShopItem(
    val type: JarType,
    val name: String,
    val description: String,
    val price: Int,
    val requiredLevel: Int
)

@Composable
private fun JarCard(
    jar: JarShopItem,
    isUnlocked: Boolean,
    canAfford: Boolean,
    hasLevel: Boolean,
    onBuy: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "🏺",
                    fontSize = 40.sp
                )
                Spacer(modifier = Modifier.width(16.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = jar.name,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        if (isUnlocked) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "✓",
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                    Text(
                        text = jar.description,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "Capacity: ${GameLogic.getJarCapacity(jar.type)} plants • Level ${jar.requiredLevel}+",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Button(
                onClick = onBuy,
                modifier = Modifier.fillMaxWidth(),
                enabled = !isUnlocked && canAfford && hasLevel
            ) {
                Text(if (isUnlocked) "Unlocked" else if (!hasLevel) "Level ${jar.requiredLevel} Required" else "${jar.price} 🪙")
            }
        }
    }
}

@Composable
private fun DecorationCard(
    item: ShopItem,
    canAfford: Boolean,
    hasLevel: Boolean,
    onBuy: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = item.emoji, fontSize = 32.sp)
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = item.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = item.description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                if (item.requiredLevel > 1) {
                    Text(
                        text = "Level ${item.requiredLevel}+",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    )
                }
            }
            
            Button(
                onClick = onBuy,
                enabled = canAfford && hasLevel
            ) {
                Text("${item.price} 🪙")
            }
        }
    }
}