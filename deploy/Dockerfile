FROM node:20-alpine AS build
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app /app
EXPOSE 18791
USER node
CMD ["node", "packages/gateway/dist/cli.js"]
