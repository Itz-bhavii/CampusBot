# Stage 1: Build the application using Maven
FROM maven:3-eclipse-temurin-17 AS build
WORKDIR /app

# Copy the pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy the source code and build the application
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Create the final, lightweight image
FROM eclipse-temurin:17-jre
WORKDIR /app
# Copy the built JAR file from the 'build' stage
COPY --from=build /app/target/campusbot-0.0.1-SNAPSHOT.jar app.jar
# Expose the port the app runs on
EXPOSE 8080
# Command to run the application
ENTRYPOINT ["java", "-jar", "app.jar"]