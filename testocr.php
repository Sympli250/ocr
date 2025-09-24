<?php
// Page de test pour Symplissime OCR API
// Réalisé par Ayi NEDJIMI Consultants
// Version 1.2.0

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $file = $_FILES["document"]["tmp_name"];
    $profile = $_POST["profile"];
    $format = $_POST["format"];
    $enhance = $_POST["enhance"];

    $url = "http://localhost:8000/ocr?profile=$profile&output_format=$format";
    if (!empty($enhance)) {
        $url .= "&enhance=$enhance";
    }

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, [
        "file" => new CURLFile($file, $_FILES["document"]["type"], $_FILES["document"]["name"])
    ]);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    echo "<h2>Résultat OCR :</h2>";

    // Vérification de la réponse
    if ($response === FALSE) {
        echo "<div class='error'>Erreur de connexion à l'API OCR</div>";
    } else {
        // Vérification du code HTTP
        if ($httpCode !== 200) {
            echo "<div class='error'>Erreur API (Code: $httpCode)</div>";
            echo "<pre>" . htmlspecialchars($response) . "</pre>";
        } else {
            if ($format === "json") {
                // Validation JSON avant affichage
                $jsonData = json_decode($response, true);
                if (json_last_error() === JSON_ERROR_NONE) {
                    echo "<pre>" . htmlspecialchars(json_encode($jsonData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) . "</pre>";
                } else {
                    echo "<div class='error'>Réponse JSON invalide</div>";
                    echo "<pre>" . htmlspecialchars($response) . "</pre>";
                }
            } elseif ($format === "html") {
                // Validation HTML basique et échappement sélectif
                if (strpos($response, '<html>') !== false && strpos($response, '</html>') !== false) {
                    // Nettoyage basique - autorise seulement les balises HTML sûres
                    $allowedTags = '<html><head><body><title><meta><style><h1><h2><h3><div><p><span><strong><em><ul><ol><li><br><pre>';
                    echo strip_tags($response, $allowedTags);
                } else {
                    echo "<div class='error'>Réponse HTML invalide</div>";
                    echo "<pre>" . htmlspecialchars($response) . "</pre>";
                }
            } else {
                // Format texte - toujours échapper
                echo "<pre>" . htmlspecialchars($response) . "</pre>";
            }
        }
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Symplissime OCR</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .error {
            color: red;
            font-weight: bold;
            padding: 10px;
            background-color: #ffe6e6;
            border: 1px solid #ff9999;
            border-radius: 4px;
            margin: 10px 0;
        }
        h1 { color: #333; }
        form { background: #f9f9f9; padding: 20px; border-radius: 8px; }
        label { display: block; margin-top: 10px; font-weight: bold; }
        input, select, button { margin-top: 5px; padding: 8px; }
        button { background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        pre { background: #f0f0f0; padding: 15px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Test OCR API <small style="color:#666;">(v1.2.0)</small></h1>
    <form method="post" enctype="multipart/form-data">
        <label>Choisir un document :</label><br>
        <input type="file" name="document" required><br><br>

        <label>Profil :</label>
        <select name="profile">
            <option value="printed">📄 Imprimé</option>
            <option value="handwriting">✍️ Manuscrit</option>
            <option value="legal">⚖️ Juridique</option>
            <option value="scanned">🖨️ Scanné</option>
            <option value="english">🇬🇧 Anglais</option>
            <option value="multilang">🌍 Multi-langue</option>
        </select><br><br>

        <label>Format de sortie :</label>
        <select name="format">
            <option value="text">Texte</option>
            <option value="json">JSON</option>
            <option value="html">HTML</option>
        </select><br><br>

        <label>Amélioration image :</label>
        <select name="enhance">
            <option value="">Aucune</option>
            <option value="contrast">Contraste</option>
            <option value="sharpness">Netteté</option>
            <option value="brightness">Luminosité</option>
            <option value="defloutage">Défloutage</option>
        </select><br><br>

        <button type="submit">Envoyer</button>
    </form>
</body>
</html>
