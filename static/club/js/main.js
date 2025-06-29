// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
            target.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    });
});

// Add scroll animations
const observerOptions = {threshold: 0.1, rootMargin: '0px 0px -50px 0px'};
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            Object.assign(entry.target.style, {
                opacity: '1',
                transform: 'translateY(0)'
            });
        }
    });
});

// Initialize animation for target elements
document.querySelectorAll('.feature-card, .training-card').forEach(card => {
    Object.assign(card.style, {
        opacity: '0',
        transform: 'translateY(20px)',
        transition: 'all 0.6s ease'
    });
    observer.observe(card);
});

// Interactive button effects (ripple)
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', e => {
        const ripple = document.createElement('span');
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        Object.assign(ripple.style, {
            position: 'absolute',
            borderRadius: '50%',
            width: `${size}px`,
            height: `${size}px`,
            left: `${e.clientX - rect.left - size / 2}px`,
            top: `${e.clientY - rect.top - size / 2}px`,
            background: 'rgba(255,255,255,0.6)',
            transform: 'scale(0)',
            animation: 'ripple 0.6s linear',
            pointerEvents: 'none'
        });
        btn.appendChild(ripple);
        ripple.addEventListener('animationend', () => ripple.remove());
    });
});

// Add ripple animation CSS
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    .btn {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(rippleStyle);

// Alert handling
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.transition = 'opacity 0.5s ease-in-out';

        const removeAlert = () => {
            alert.animate([{opacity: 1}, {opacity: 0}], {duration: 500})
                .addEventListener('finish', () => alert.remove());
        };

        setTimeout(removeAlert, 5000);

        const closeButton = alert.querySelector('.close-alert, .btn-close, [data-dismiss="alert"], .alert-close');
        if (closeButton) {
            closeButton.addEventListener('click', e => {
                e.preventDefault();
                removeAlert();
            });
        } else {
            alert.addEventListener('click', () => removeAlert());
        }
    });
});

// Mobile navigation
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navMenu = document.querySelector('.nav-menu');

    if (mobileMenuBtn && navMenu) {
        const toggleMenu = () => {
            navMenu.classList.toggle('active');
            const icon = mobileMenuBtn.querySelector('i');
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        };

        mobileMenuBtn.addEventListener('click', toggleMenu);

        document.querySelectorAll('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => navMenu.classList.remove('active'));
        });

        document.addEventListener('click', e => {
            if (!navMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
});
