# Ayuda de extracción

TravelBot utiliza Gemini para interpretar la conversación y extraer los datos necesarios del viaje. Para obtener información adicional, preferimos la API **Google AI Overview** de SerpAPI en lugar de `engine=google`. Primero se hace una búsqueda para conseguir `ai_overview.page_token` y luego se consulta el endpoint `search?engine=google_ai_overview` con ese token.

Esta API devuelve resúmenes de las páginas de resultados de Google, lo que facilita obtener rápidamente:

- Códigos IATA de aeropuertos o ciudades.
- Direcciones de lugares y sitios de interés.
- Nivel de riesgo o seguridad de una zona o barrio.

El resumen se analiza para extraer estos datos y acelerar las consultas. Se utiliza principalmente cuando no se encuentran los códigos IATA o se necesita validar la seguridad de una zona antes de sugerir hoteles.
