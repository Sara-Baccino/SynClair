import polars as pl
from synclair_core.models.data_config import DataConfig
from synclair_core.models.column_info import ColumnInfo
from synclair_core.dataset.preprocessing import Preprocessing

from synclair_structure.config.structure_module_config import StructureModuleConfig
from synclair_structure.config.clustering_configs import KMeansConfig
from synclair_structure.config.projection_configs import PCAConfig
from synclair_structure.pipeline.structure_module import StructureModule


def test_structure_e2e_flow():
    # 1. Dataset sintetico
    df = pl.DataFrame({
        "feature1": [1.0, 2.0, 10.0, 11.0, 1.5, 10.5],
        "feature2": [1.1, 1.9, 9.8, 10.2, 1.4, 10.1],
    })

    # 2. Configurazione Colonne (marcate come numerical=True)
    columns_spec = {
        "feature1": ColumnInfo(new_name="feature1", numerical=True, active=True),
        "feature2": ColumnInfo(new_name="feature2", numerical=True, active=True),
    }
    data_config = DataConfig(columns=columns_spec)
    processed_df = Preprocessing.run(df, data_config)

    # 3. Configurazione StructureModule (PCA + KMeans)
    structure_config = StructureModuleConfig(
        projection_algorithm="pca",
        projection_config=PCAConfig(n_components=2),
        clustering_algorithm="kmeans",
        clustering_config=KMeansConfig(n_clusters=2),
    )

    # 4. Fit e Run
    structure_module = StructureModule()
    structure_module.fit(
        dataset=processed_df,
        data_config=data_config,
        module_config=structure_config,
    )
    result = structure_module.run()

    # 5. Assertions
    assert result.success, f"Pipeline fallita con errore: {result.error}"

    clustered_df = result.datasets.get("clustered_dataset")
    assert clustered_df is not None, "Il dataset 'clustered_dataset' non è stato generato"
    assert "cluster_label" in clustered_df.columns
    print("✅ Test E2E completato con successo!")


if __name__ == "__main__":
    test_structure_e2e_flow()