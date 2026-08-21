FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["CoreBankingMigration.Api.csproj", "./"]
RUN dotnet restore "CoreBankingMigration.Api.csproj"
COPY . .
RUN dotnet build "CoreBankingMigration.Api.csproj" -c Release -o /app/build
RUN dotnet publish "CoreBankingMigration.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 5000
ENV ASPNETCORE_URLS=http://+:5000
ENTRYPOINT ["dotnet", "CoreBankingMigration.Api.dll"]
