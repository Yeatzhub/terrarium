package com.terrarium.app.di

import android.content.Context
import com.terrarium.app.data.database.*
import com.terrarium.app.data.repository.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): TerrariumDatabase {
        return TerrariumDatabase.getDatabase(context)
    }
    
    @Provides
    fun provideTerrariumDao(database: TerrariumDatabase): TerrariumDao {
        return database.terrariumDao()
    }
    
    @Provides
    fun providePlantDao(database: TerrariumDatabase): PlantDao {
        return database.plantDao()
    }
    
    @Provides
    fun providePlantTypeDao(database: TerrariumDatabase): PlantTypeDao {
        return database.plantTypeDao()
    }
    
    @Provides
    fun provideInventoryDao(database: TerrariumDatabase): InventoryDao {
        return database.inventoryDao()
    }
    
    @Provides
    fun provideUserDao(database: TerrariumDatabase): UserDao {
        return database.userDao()
    }
    
    @Provides
    fun provideDailyTaskDao(database: TerrariumDatabase): DailyTaskDao {
        return database.dailyTaskDao()
    }
    
    @Provides
    fun provideCuttingDao(database: TerrariumDatabase): CuttingDao {
        return database.cuttingDao()
    }
}

@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {
    
    @Provides
    @Singleton
    fun provideTerrariumRepository(dao: TerrariumDao): TerrariumRepository {
        return TerrariumRepository(dao)
    }
    
    @Provides
    @Singleton
    fun providePlantRepository(dao: PlantDao): PlantRepository {
        return PlantRepository(dao)
    }
    
    @Provides
    @Singleton
    fun providePlantTypeRepository(dao: PlantTypeDao): PlantTypeRepository {
        return PlantTypeRepository(dao)
    }
    
    @Provides
    @Singleton
    fun provideInventoryRepository(dao: InventoryDao): InventoryRepository {
        return InventoryRepository(dao)
    }
    
    @Provides
    @Singleton
    fun provideUserRepository(dao: UserDao): UserRepository {
        return UserRepository(dao)
    }
    
    @Provides
    @Singleton
    fun provideDailyTaskRepository(dao: DailyTaskDao): DailyTaskRepository {
        return DailyTaskRepository(dao)
    }
    
    @Provides
    @Singleton
    fun provideCuttingRepository(dao: CuttingDao): CuttingRepository {
        return CuttingRepository(dao)
    }
}