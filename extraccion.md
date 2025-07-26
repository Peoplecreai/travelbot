# Ayuda de extracción

TravelBot utiliza Gemini para interpretar la conversación y extraer los datos necesarios del viaje. Para obtener información adicional, preferimos la API **Google AI Overview** de SerpAPI en lugar de `engine=google`. Primero se hace una búsqueda para conseguir `ai_overview.page_token` y luego se consulta el endpoint `search?engine=google_ai_overview` con ese token.

Esta API devuelve resúmenes de las páginas de resultados de Google, lo que facilita obtener rápidamente:
=======
TravelBot utiliza Gemini para interpretar la conversación y extraer los datos necesarios del viaje. Para complementar esta información podemos usar la API **Google AI Overview** de SerpAPI. Esta API devuelve resúmenes de las páginas de resultados de Google y permite obtener rápidamente detalles como:

- Códigos IATA de aeropuertos o ciudades.
- Direcciones de lugares y sitios de interés.
- Nivel de riesgo o seguridad de una zona o barrio.

El resumen se analiza para extraer estos datos y acelerar las consultas. Se utiliza principalmente cuando no se encuentran los códigos IATA o se necesita validar la seguridad de una zona antes de sugerir hoteles.
=======
Para usarla, solicita un `ai_overview.page_token` al realizar una búsqueda con SerpAPI y luego llama al endpoint `search?engine=google_ai_overview` con ese token. El resumen obtenido puede analizarse para extraer las piezas de información anteriores y acelerar el proceso de consulta.

Esta técnica se usa como apoyo cuando no se encuentran los códigos IATA o cuando se necesita validar si una zona es segura antes de sugerir hoteles.
