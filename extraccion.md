# Ayuda de extracción

TravelBot utiliza Gemini para interpretar la conversación y extraer los datos necesarios del viaje. Para complementar esta información preferimos usar la API **Google AI Overview** de SerpAPI en lugar de la búsqueda tradicional con `engine=google`. Primero se realiza una búsqueda para obtener `ai_overview.page_token` y luego se consulta `search?engine=google_ai_overview` con ese token.

Esta API devuelve un resumen que facilita la obtención rápida de:

- Códigos IATA de aeropuertos o ciudades.
- Direcciones de lugares y sitios de interés.
- Nivel de riesgo o seguridad de una zona o barrio.

El resumen se analiza para extraer estas piezas y agilizar las consultas. Esta técnica se usa cuando no se encuentran los códigos IATA o se necesita validar si una zona es segura antes de sugerir hoteles.
