# -*- coding: utf-8 -*-
"""streamlit_app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1DsR2XPYVrHrqIFZRiyiLWS0OV5wB38pU
"""


# model.py
import torch
import torch.nn as nn
import torch.nn.functional as F

import torchvision
from torchvision import transforms
from torch.utils.data import DataLoader
class VAE(nn.Module):
    def __init__(self, latent_dim=20):
        super(VAE, self).__init__()
        self.fc1 = nn.Linear(784, 400)
        self.fc21 = nn.Linear(400, latent_dim)  # mu
        self.fc22 = nn.Linear(400, latent_dim)  # logvar
        self.fc3 = nn.Linear(latent_dim, 400)
        self.fc4 = nn.Linear(400, 784)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        return self.fc21(h1), self.fc22(h1)  # mu, logvar

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h3))

    def forward(self, x):
        mu, logvar = self.encode(x.view(-1, 784))
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

def vae_loss(recon_x, x, mu, logvar):
    BCE = F.binary_cross_entropy(recon_x, x.view(-1, 784), reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return BCE + KLD

transform = transforms.ToTensor()

train_dataset = torchvision.datasets.MNIST(root='./data', train=True, transform=transform, download=True)
train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = VAE().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

epochs = 10  # You can adjust this
for epoch in range(epochs):
    model.train()
    train_loss = 0
    for batch_idx, (data, _) in enumerate(train_loader):
        data = data.to(device)
        optimizer.zero_grad()
        recon_batch, mu, logvar = model(data)
        loss = vae_loss(recon_batch, data, mu, logvar)
        loss.backward()
        train_loss += loss.item()
        optimizer.step()

    print(f'Epoch {epoch+1}, Loss: {train_loss / len(train_loader.dataset):.4f}')

torch.save(model.state_dict(), 'model.pth')

import streamlit as st
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import matplotlib.pyplot as plt

# VAE Definition
class VAE(nn.Module):
    def __init__(self, latent_dim=20):
        super(VAE, self).__init__()
        self.fc1 = nn.Linear(784, 400)
        self.fc21 = nn.Linear(400, latent_dim)
        self.fc22 = nn.Linear(400, latent_dim)
        self.fc3 = nn.Linear(latent_dim, 400)
        self.fc4 = nn.Linear(400, 784)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        return self.fc21(h1), self.fc22(h1)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h3))

    def forward(self, x):
        mu, logvar = self.encode(x.view(-1, 784))
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

# Load the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = VAE().to(device)
model.load_state_dict(torch.load("model.pth", map_location=device))
model.eval()

# Load MNIST dataset
@st.cache_data
def load_mnist():
    mnist_data = torchvision.datasets.MNIST(
        root='./data', train=True, download=True,
        transform=torchvision.transforms.ToTensor()
    )
    data_loader = torch.utils.data.DataLoader(mnist_data, batch_size=60000, shuffle=False)
    return next(iter(data_loader))

images, labels = load_mnist()

# Streamlit UI
st.title("🧠 Handwritten Digit Generator")
digit = st.selectbox("Select a digit to generate", list(range(10)))

# Generate and display
st.subheader(f"Generated images for digit: {digit}")
fig, axes = plt.subplots(1, 5, figsize=(10, 2))

digit_tensors = images[labels == digit]

for i in range(5):
    idx = torch.randint(len(digit_tensors), (1,)).item()
    img = digit_tensors[idx].to(device)
    with torch.no_grad():
        mu, logvar = model.encode(img.view(-1, 784))
        z = model.reparameterize(mu, logvar)
        out = model.decode(z).view(28, 28).cpu().numpy()
    axes[i].imshow(out, cmap="gray")
    axes[i].axis("off")

st.pyplot(fig)
