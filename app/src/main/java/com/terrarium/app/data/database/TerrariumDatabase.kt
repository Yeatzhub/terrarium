package com.terrarium.app.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import com.terrarium.app.data.model.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Database(
    entities = [
        Terrarium::class,
        Plant::class,
        PlantType::class,
        InventoryItem::class,
        User::class,
        DailyTask::class,
        Cutting::class
    ],
    version = 2,
    exportSchema = false
)
abstract class TerrariumDatabase : RoomDatabase() {
    
    abstract fun terrariumDao(): TerrariumDao
    abstract fun plantDao(): PlantDao
    abstract fun plantTypeDao(): PlantTypeDao
    abstract fun inventoryDao(): InventoryDao
    abstract fun userDao(): UserDao
    abstract fun dailyTaskDao(): DailyTaskDao
    abstract fun cuttingDao(): CuttingDao
    
    companion object {
        @Volatile
        private var INSTANCE: TerrariumDatabase? = null
        
        fun getDatabase(context: Context): TerrariumDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    TerrariumDatabase::class.java,
                    "terrarium_database"
                )
                    .addCallback(DatabaseCallback())
                    .fallbackToDestructiveMigration() // For development, will be removed in production
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
    
    private class DatabaseCallback(
        private val scope: CoroutineScope = CoroutineScope(Dispatchers.IO)
    ) : RoomDatabase.Callback() {
        
        override fun onCreate(db: SupportSQLiteDatabase) {
            super.onCreate(db)
            INSTANCE?.let { database ->
                scope.launch {
                    populateDatabase(database)
                }
            }
        }
        
        suspend fun populateDatabase(db: TerrariumDatabase) {
            // Pre-populate plant types
            db.plantTypeDao().insertPlantTypes(DefaultPlantTypes.ALL)
            
            // Create default user
            val userId = db.userDao().insertUser(User(name = "Gardener", coins = 100))
            
            // Create starter terrarium
            db.terrariumDao().insertTerrarium(
                Terrarium(
                    name = "My First Terrarium",
                    jarType = JarType.SMALL,
                    level = 1
                )
            )
        }
    }
}