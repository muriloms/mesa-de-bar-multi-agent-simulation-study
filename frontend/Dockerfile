# Estágio 1: Builder - Compila a aplicação React
FROM node:20-alpine as builder

WORKDIR /app

# Copia os arquivos de definição do projeto e instala as dependências
COPY package.json package-lock.json ./
RUN npm install

# Copia o restante do código-fonte
COPY . .

# Argumento de build para a URL da API, que será passado pelo Docker Compose
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Executa o build de produção
RUN npm run build


# Estágio 2: Server - Serve os arquivos estáticos com Nginx
FROM nginx:stable-alpine

# Copia a configuração customizada do Nginx (criaremos a seguir)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia os arquivos compilados do estágio 'builder' para a pasta pública do Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Expõe a porta 80, que é a porta padrão do Nginx
EXPOSE 80

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]