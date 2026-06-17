FROM node:20-alpine AS dev

WORKDIR /app

RUN apk add --no-cache curl

COPY package.json ./

RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
