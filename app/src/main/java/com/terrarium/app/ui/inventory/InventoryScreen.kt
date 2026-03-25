package com.terrarium.app.ui.inventory

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.terrarium.app.data.model.*
import com.terrarium.app.viewmodel.InventoryViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun InventoryScreen(
    viewModel: InventoryViewModel = hiltViewModel(),
    onBack: () -> Unit = {}
) {
    var selectedTab by remember { mutableStateOf(0) }
    val tabs = listOf("Seeds", "Cuttings", "Decorations")
    val inventory by viewModel.inventory.collectAsState()
    
    // Group inventory by type
    val seeds = inventory.filter { it.itemType == ItemType.SEED }
    val cuttings = inventory.filter { it.itemType == ItemType.CUTTING }
    val decorations = inventory.filter { it.itemType == ItemType.DECORATION }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("📦 Inventory") },
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
            
            // Content
            when (selectedTab) {
                0 -> InventoryList(
                    items = seeds,
                    emptyMessage = "No seeds yet!\nVisit the shop to buy some.",
                    itemName = "seeds"
                )
                1 -> InventoryList(
                    items = cuttings,
                    emptyMessage = "No cuttings yet!\nPropagate mature plants to create cuttings.",
                    itemName = "cuttings"
                )
                2 -> InventoryList(
                    items = decorations,
                    emptyMessage = "No decorations yet!\nVisit the shop to buy some.",
                    itemName = "decorations"
                )
            }
        }
    }
}

@Composable
private fun InventoryList(
    items: List<InventoryItem>,
    emptyMessage: String,
    itemName: String
) {
    if (items.isEmpty()) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(text = "📦", fontSize = 48.sp)
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = emptyMessage,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    } else {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(items) { item ->
                InventoryItemCard(
                    item = item,
                    itemName = itemName
                )
            }
        }
    }
}

@Composable
private fun InventoryItemCard(
    item: InventoryItem,
    itemName: String
) {
    // Get emoji based on item type
    val emoji = when (item.itemType) {
        ItemType.SEED -> "🌱"
        ItemType.CUTTING -> "🌿"
        ItemType.DECORATION -> "🎨"
        ItemType.JAR_UNLOCK -> "🏺"
        ItemType.FERTILIZER -> "🧪"
        ItemType.WATERING_CAN -> "💧"
        ItemType.PESTICIDE -> "🛡️"
    }
    
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
            Text(text = emoji, fontSize = 32.sp)
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = when (item.itemType) {
                        ItemType.SEED -> "Seed Packet #${item.itemId}"
                        ItemType.CUTTING -> "Cutting #${item.itemId}"
                        else -> "Item #${item.itemId}"
                    },
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "x${item.quantity}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            
            FilledTonalButton(onClick = { /* use item */ }) {
                Text("Use")
            }
        }
    }
}