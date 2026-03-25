package com.terrarium.app.ui.home

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.terrarium.app.data.model.*
import com.terrarium.app.util.GameLogic
import com.terrarium.app.viewmodel.HomeViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HomeViewModel = hiltViewModel(),
    onNavigateToShop: () -> Unit = {},
    onNavigateToInventory: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {}
) {
    val user by viewModel.user.collectAsState()
    val terrariums by viewModel.terrariums.collectAsState()
    val selectedTerrarium by viewModel.selectedTerrarium.collectAsState()
    val plants by viewModel.plants.collectAsState()
    val dailyTasks by viewModel.dailyTasks.collectAsState()
    val plantTypes by viewModel.plantTypes.collectAsState()
    val message by viewModel.message.collectAsState()
    
    var showPlantDialog by remember { mutableStateOf(false) }
    var showWaterDialog by remember { mutableStateOf(false) }
    var showPropagateDialog by remember { mutableStateOf(false) }
    var selectedPlant by remember { mutableStateOf<Plant?>(null) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "🌿 Terrarium",
                            fontWeight = FontWeight.Bold
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                ),
                actions = {
                    // Coins display
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
                    IconButton(onClick = { /* notifications */ }) {
                        Badge(
                            content = { 
                                if (viewModel.plantsNeedingWater.value.isNotEmpty()) {
                                    Text("${viewModel.plantsNeedingWater.value.size}")
                                }
                            }
                        ) {
                            Icon(Icons.Default.Notifications, "Notifications")
                        }
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, "Settings")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Level & XP Bar
            item {
                if (user != null) {
                    LevelIndicator(
                        level = user!!.level,
                        xp = user!!.xp,
                        xpToNext = user!!.xpToNextLevel(),
                        coins = user!!.coins
                    )
                }
            }
            
            // Daily Tasks Section
            item {
                DailyTasksSection(
                    tasks = dailyTasks,
                    onCompleteTask = { taskId -> viewModel.completeTask(taskId) }
                )
            }
            
            // Terrarium Selection
            item {
                TerrariumSelector(
                    terrariums = terrariums,
                    selectedId = selectedTerrarium?.id,
                    onSelect = { viewModel.selectTerrarium(it) },
                    onCreate = { viewModel.createTerrarium("New Terrarium", JarType.SMALL) }
                )
            }
            
            // Plant Display
            item {
                TerrariumJar(
                    jarType = selectedTerrarium?.jarType ?: JarType.SMALL,
                    plants = plants,
                    plantTypes = plantTypes.associateBy { it.id },
                    onPlantClick = { plant ->
                        selectedPlant = plant
                        showPlantDialog = true
                    }
                )
            }
            
            // Quick Actions
            item {
                QuickActions(
                    onWaterAll = { showWaterDialog = true },
                    onPlant = { showPlantDialog = true },
                    onPropagate = { showPropagateDialog = true }
                )
            }
            
            // Plants List (for easier management)
            item {
                PlantsSection(
                    plants = plants,
                    plantTypes = plantTypes.associateBy { it.id },
                    onWater = { viewModel.waterPlant(it) },
                    onPropagate = {
                        selectedPlant = it
                        viewModel.propagatePlant(it.id)
                    }
                )
            }
        }
        
        // Show message snackbar
        message?.let { msg ->
            LaunchedEffect(msg) {
                // Show snackbar (would typically use SnackbarHostState)
            }
        }
    }
    
    // Plant Detail Dialog
    if (showPlantDialog && selectedPlant != null) {
        PlantDetailDialog(
            plant = selectedPlant!!,
            plantType = viewModel.getPlantType(selectedPlant!!.typeId),
            onDismiss = { showPlantDialog = false },
            onWater = {
                viewModel.waterPlant(selectedPlant!!.id)
                showPlantDialog = false
            },
            onPropagate = {
                viewModel.propagatePlant(selectedPlant!!.id)
                showPlantDialog = false
            }
        )
    }
    
    // Water All Dialog
    if (showWaterDialog) {
        AlertDialog(
            onDismissRequest = { showWaterDialog = false },
            title = { Text("Water All Plants") },
            text = { Text("Water all plants in this terrarium? This will take some time.") },
            confirmButton = {
                Button(onClick = {
                    viewModel.waterAllPlants()
                    showWaterDialog = false
                }) {
                    Text("Water All")
                }
            },
            dismissButton = {
                TextButton(onClick = { showWaterDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
private fun LevelIndicator(level: Int, xp: Long, xpToNext: Long, coins: Int) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Level badge
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "$level",
                    color = MaterialTheme.colorScheme.onPrimary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp
                )
            }
            
            Spacer(modifier = Modifier.width(12.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Level $level Gardener",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                // XP Progress bar
                LinearProgressIndicator(
                    progress = { if (xpToNext > 0) (xp.toFloat() / xpToNext.toFloat()) else 1f },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp)),
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "$xp / $xpToNext XP",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun DailyTasksSection(
    tasks: List<DailyTask>,
    onCompleteTask: (Long) -> Unit
) {
    if (tasks.isEmpty()) return
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "📋 Daily Tasks",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(12.dp))
            
            tasks.forEach { task ->
                DailyTaskItem(
                    task = task,
                    onComplete = { onCompleteTask(task.id) }
                )
                if (task != tasks.last()) {
                    Spacer(modifier = Modifier.height(8.dp))
                }
            }
        }
    }
}

@Composable
private fun DailyTaskItem(
    task: DailyTask,
    onComplete: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = !task.isCompleted && task.currentCount >= task.targetCount) { onComplete() }
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Task icon
        Text(
            text = when (task.taskType) {
                TaskType.WATER_PLANTS -> "💧"
                TaskType.PROPAGATE_PLANT -> "✂️"
                TaskType.CHECK_TERRARIUM -> "👀"
                TaskType.BUY_ITEM -> "🛒"
                TaskType.PLANT_SEED -> "🌱"
                TaskType.HARVEST_PLANT -> "🌾"
                TaskType.LOGIN -> "👋"
                TaskType.KEEP_PLANTS_HEALTHY -> "❤️"
            },
            fontSize = 24.sp
        )
        
        Spacer(modifier = Modifier.width(12.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = task.name,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = if (task.isCompleted) FontWeight.Normal else FontWeight.Bold,
                color = if (task.isCompleted) 
                    MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f) 
                else 
                    MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = task.description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        
        // Progress or completed
        if (task.isCompleted) {
            Text(
                text = "✓",
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
                fontSize = 20.sp
            )
        } else {
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "${task.currentCount}/${task.targetCount}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "+${task.xpReward} XP",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
private fun TerrariumSelector(
    terrariums: List<Terrarium>,
    selectedId: Long?,
    onSelect: (Long) -> Unit,
    onCreate: () -> Unit
) {
    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(terrariums) { terrarium ->
            FilterChip(
                selected = terrarium.id == selectedId,
                onClick = { onSelect(terrarium.id) },
                label = { Text(terrarium.name) }
            )
        }
        
        item {
            FilterChip(
                selected = false,
                onClick = onCreate,
                label = { Text("+ New") }
            )
        }
    }
}

@Composable
private fun TerrariumJar(
    jarType: JarType,
    plants: List<Plant>,
    plantTypes: Map<Long, PlantType>,
    onPlantClick: (Plant) -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(0.7f)
            .clip(RoundedCornerShape(32.dp))
            .border(
                width = 4.dp,
                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f),
                shape = RoundedCornerShape(32.dp)
            )
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFFB2DFDB).copy(alpha = 0.3f),
                        Color(0xFF80CBC4).copy(alpha = 0.2f)
                    )
                )
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // Jar name
            Text(
                text = when (jarType) {
                    JarType.SMALL -> "Small Jar"
                    JarType.MEDIUM -> "Medium Jar"
                    JarType.ROUND -> "Round Jar"
                    JarType.WIDE -> "Wide Jar"
                    JarType.TALL -> "Tall Jar"
                },
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            if (plants.isEmpty()) {
                Text(
                    text = "🌿",
                    fontSize = 64.sp,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                Text(
                    text = "Your terrarium is empty!\nPlant some seeds to get started",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f),
                    textAlign = TextAlign.Center
                )
            } else {
                // Show plant emojis
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(plants) { plant ->
                        val plantType = plantTypes[plant.typeId]
                        PlantCard(
                            plant = plant,
                            plantType = plantType,
                            onClick = { onPlantClick(plant) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PlantCard(
    plant: Plant,
    plantType: PlantType?,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .size(80.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = when (plant.getStatus()) {
                PlantStatus.HEALTHY -> Color(0xFF4CAF50).copy(alpha = 0.2f)
                PlantStatus.FAIR -> Color(0xFFFFEB3B).copy(alpha = 0.2f)
                PlantStatus.UNHEALTHY -> Color(0xFFFF9800).copy(alpha = 0.2f)
                PlantStatus.WILTING -> Color(0xFFFF5722).copy(alpha = 0.2f)
                PlantStatus.OVERWATERED -> Color(0xFF2196F3).copy(alpha = 0.2f)
                PlantStatus.DEAD -> Color.Gray.copy(alpha = 0.2f)
            }
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = plantType?.emoji ?: "🌱",
                fontSize = 28.sp
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = plant.growthStage.name.lowercase().capitalize(),
                style = MaterialTheme.typography.labelSmall,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

@Composable
private fun QuickActions(
    onWaterAll: () -> Unit,
    onPlant: () -> Unit,
    onPropagate: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        QuickActionButton(
            icon = "💧",
            label = "Water All",
            modifier = Modifier.weight(1f),
            onClick = onWaterAll
        )
        
        QuickActionButton(
            icon = "🌱",
            label = "Plant",
            modifier = Modifier.weight(1f),
            onClick = onPlant
        )
        
        QuickActionButton(
            icon = "✂️",
            label = "Propagate",
            modifier = Modifier.weight(1f),
            onClick = onPropagate
        )
    }
}

@Composable
private fun QuickActionButton(
    icon: String,
    label: String,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(56.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = icon, fontSize = 20.sp)
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSecondaryContainer
            )
        }
    }
}

@Composable
private fun PlantsSection(
    plants: List<Plant>,
    plantTypes: Map<Long, PlantType>,
    onWater: (Long) -> Unit,
    onPropagate: (Plant) -> Unit
) {
    if (plants.isEmpty()) return
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "🌿 Your Plants",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(12.dp))
            
            plants.forEach { plant ->
                val plantType = plantTypes[plant.typeId]
                PlantListItem(
                    plant = plant,
                    plantType = plantType,
                    onWater = { onWater(plant.id) },
                    onPropagate = { onPropagate(plant) }
                )
                if (plant != plants.last()) {
                    HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                }
            }
        }
    }
}

@Composable
private fun PlantListItem(
    plant: Plant,
    plantType: PlantType?,
    onWater: () -> Unit,
    onPropagate: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = plantType?.emoji ?: "🌱", fontSize = 32.sp)
        Spacer(modifier = Modifier.width(12.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = plantType?.name ?: "Unknown Plant",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "${plant.growthStage.name.lowercase().capitalize()} • ${plant.getStatus().getDisplayName()}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            // Moisture indicator
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "💧",
                    fontSize = 12.sp
                )
                LinearProgressIndicator(
                    progress = { plant.moisture },
                    modifier = Modifier
                        .weight(1f)
                        .height(4.dp)
                        .padding(horizontal = 4.dp),
                )
                Text(
                    text = "${(plant.moisture * 100).toInt()}%",
                    style = MaterialTheme.typography.labelSmall
                )
            }
        }
        
        // Action buttons
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (!plant.isDead && plant.moisture < 0.8f) {
                IconButton(onClick = onWater) {
                    Icon(Icons.Default.WaterDrop, "Water plant")
                }
            }
            if (plant.canPropagate()) {
                IconButton(onClick = onPropagate) {
                    Text("✂️", fontSize = 20.sp)
                }
            }
        }
    }
}

@Composable
private fun PlantDetailDialog(
    plant: Plant,
    plantType: PlantType?,
    onDismiss: () -> Unit,
    onWater: () -> Unit,
    onPropagate: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(plantType?.name ?: "Unknown Plant") },
        text = {
            Column {
                Text(text = plantType?.scientificName ?: "", style = MaterialTheme.typography.bodySmall)
                Spacer(modifier = Modifier.height(16.dp))
                
                // Status
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = plant.getStatus().getEmoji(), fontSize = 24.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = plant.getStatus().getDisplayName())
                }
                
                Spacer(modifier = Modifier.height(12.dp))
                
                // Growth stage
                Text(text = "Growth: ${plant.growthStage.name.lowercase().capitalize()}")
                
                // Health
                Text(text = "Health: ${plant.health}%")
                
                // Moisture
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "Moisture: ${(plant.moisture * 100).toInt()}%")
                    if (plant.moisture < 0.3f) {
                        Text(
                            text = " - Needs water!",
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
                
                // Time until next stage
                plantType?.let {
                    val hoursRemaining = plant.timeToNextStage(it)
                    if (hoursRemaining > 0) {
                        Text(text = "Next stage in: ${hoursRemaining}h")
                    }
                }
            }
        },
        confirmButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (!plant.isDead && plant.moisture < 0.8f) {
                    OutlinedButton(onClick = onWater) {
                        Icon(Icons.Default.WaterDrop, contentDescription = null)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Water")
                    }
                }
                if (plant.canPropagate()) {
                    Button(onClick = onPropagate) {
                        Text("✂️ Propagate")
                    }
                }
                TextButton(onClick = onDismiss) {
                    Text("Close")
                }
            }
        }
    )
}