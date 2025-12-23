# ml-service/app/model/trainer.py
import pandas as pd
import os
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from model.feature_engineer import FeatureEngineer

MODEL_PATH = os.path.join("models", "nba_xgb_model.pkl")

class Trainer:
    """
    Clase para entrenar el modelo de predicción NBA
    """
    
    def __init__(self, data_csv="data/nba_games_clean.csv"):
        """
        Args:
            data_csv: Ruta al archivo CSV con datos históricos de partidos
        """
        self.data_csv = data_csv
        self.engineer = FeatureEngineer()
        
        # Crear directorio de modelos si no existe
        os.makedirs("models", exist_ok=True)
    
    def load_data(self):
        """Carga el dataset desde CSV"""
        if not os.path.exists(self.data_csv):
            raise FileNotFoundError(f"❌ Dataset no encontrado: {self.data_csv}")
        
        print(f" Cargando datos desde {self.data_csv}...")
        
        #  CORRECCIÓN: No especificar parse_dates o usar 'game_date' si existe
        try:
            # Intentar con 'date'
            df = pd.read_csv(self.data_csv, parse_dates=["date"])
        except ValueError:
            # Si falla, intentar con 'game_date'
            try:
                df = pd.read_csv(self.data_csv, parse_dates=["game_date"])
            except ValueError:
                # Si ambos fallan, cargar sin parse_dates
                df = pd.read_csv(self.data_csv)
        
        print(f" {len(df)} partidos cargados")
        
        return df
    
    def train(self, test_size=0.2, random_state=42):
        """
        Entrena el modelo XGBoost
        
        Args:
            test_size: Proporción de datos para validación (default: 0.2)
            random_state: Semilla para reproducibilidad (default: 42)
        
        Returns:
            Modelo entrenado
        """
        print("\n" + "="*60)
        print("🎓 INICIANDO ENTRENAMIENTO")
        print("="*60 + "\n")
        
        # 1. Cargar datos
        df = self.load_data()
        
        # 2. Feature engineering
        print("\n🔧 Aplicando feature engineering...")
        features = self.engineer.build_features_from_csv(df)
        
        # 3. Separar features y target
        X = features.drop(columns=["winner"])
        y = features["winner"].astype(int)
        
        print(f"\n Features shape: {X.shape}")
        print(f" Distribución de clases:")
        print(f"   - Home wins: {y.sum()} ({y.mean():.1%})")
        print(f"   - Away wins: {len(y) - y.sum()} ({1 - y.mean():.1%})")
        
        # 4. Split train/validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state, 
            stratify=y
        )
        
        print(f"\n Train set: {len(X_train)} partidos")
        print(f" Validation set: {len(X_val)} partidos")
        
        # 5. Entrenar modelo XGBoost
        print("\n Entrenando XGBoost...")
        
        model = XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=random_state,
            n_jobs=-1
        )
        
        #  CORRECCIÓN: early_stopping_rounds ahora va en el constructor
        model = XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=random_state,
            n_jobs=-1,
            early_stopping_rounds=30  
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=50
        )
        
        # 6. Evaluar modelo
        print("\n" + "="*60)
        print(" EVALUACIÓN DEL MODELO")
        print("="*60 + "\n")
        
        # Predicciones
        train_preds = model.predict(X_train)
        val_preds = model.predict(X_val)
        
        train_proba = model.predict_proba(X_train)[:, 1]
        val_proba = model.predict_proba(X_val)[:, 1]
        
        # Métricas
        train_acc = accuracy_score(y_train, train_preds)
        val_acc = accuracy_score(y_val, val_preds)
        
        train_auc = roc_auc_score(y_train, train_proba)
        val_auc = roc_auc_score(y_val, val_proba)
        
        print(f" Train Accuracy: {train_acc:.4f}")
        print(f" Val Accuracy:   {val_acc:.4f}")
        print(f" Train AUC:      {train_auc:.4f}")
        print(f" Val AUC:        {val_auc:.4f}")
        
        # Confusion matrix
        print("\n Confusion Matrix (Validation):")
        cm = confusion_matrix(y_val, val_preds)
        print(cm)
        
        # Classification report
        print("\n Classification Report (Validation):")
        print(classification_report(y_val, val_preds, target_names=["Away Win", "Home Win"]))
        
        # Feature importance
        print("\n Top 10 Features más importantes:")
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(feature_importance.head(10).to_string(index=False))
        
        # 7. Guardar modelo
        print(f"\n Guardando modelo en {MODEL_PATH}...")
        joblib.dump(model, MODEL_PATH)
        print(" Modelo guardado exitosamente")
        
        print("\n" + "="*60)
        print(" ENTRENAMIENTO COMPLETADO")
        print("="*60 + "\n")
        
        return model

if __name__ == "__main__":
    """Ejecutar directamente para entrenar"""
    trainer = Trainer()
    trainer.train()